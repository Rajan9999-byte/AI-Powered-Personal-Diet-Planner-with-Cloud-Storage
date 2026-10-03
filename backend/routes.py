from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import login_required
from .planner import FOODS, compute_targets, food_by_id, generate_plan, validate_profile

api = Blueprint("api", __name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db():
    return current_app.extensions["db"]


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def user_payload(user: dict, profile: dict | None = None) -> dict:
    return {"id": user["id"], "email": user["email"], "name": user["name"], "profile": profile}


def serialize_profile(row: dict | None) -> dict | None:
    if not row:
        return None
    result = dict(row)
    result["allergies"] = json.loads(result.pop("allergies") or "[]")
    result["cuisines"] = json.loads(result.pop("cuisines") or "[]")
    result.pop("user_id", None)
    result.pop("updated_at", None)
    return result


def profile_from_request(payload: dict) -> dict:
    return validate_profile(payload)


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "dietly-planner-api", "storage": "sqlite-local"})


@api.post("/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    name = str(payload.get("name", "")).strip()
    if "@" not in email or len(email) > 200:
        return error("Enter a valid email address.")
    if len(password) < 8:
        return error("Password must be at least 8 characters.")
    if not name or len(name) > 80:
        return error("Name is required and must be under 80 characters.")
    user_id = uuid.uuid4().hex
    try:
        db().run(
            "INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, generate_password_hash(password), name, now_iso()),
        )
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return error("An account with that email already exists.", 409)
        raise
    session.clear()
    session["user_id"] = user_id
    return jsonify({"user": {"id": user_id, "email": email, "name": name, "profile": None}}), 201


@api.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    user = db().one("SELECT * FROM users WHERE email = ?", (email,))
    if not user or not check_password_hash(user["password_hash"], password):
        return error("Email or password is incorrect.", 401)
    session.clear()
    session["user_id"] = user["id"]
    profile = db().one("SELECT * FROM profiles WHERE user_id = ?", (user["id"],))
    return jsonify({"user": user_payload(user, serialize_profile(profile))})


@api.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@api.get("/auth/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False, "user": None})
    user = db().one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None})
    profile = db().one("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    return jsonify({"authenticated": True, "user": user_payload(user, serialize_profile(profile))})


@api.get("/profile")
@login_required
def get_profile():
    row = db().one("SELECT * FROM profiles WHERE user_id = ?", (g.user_id,))
    return jsonify({"profile": serialize_profile(row)})


@api.put("/profile")
@login_required
def save_profile():
    try:
        profile = profile_from_request(request.get_json(silent=True) or {})
    except ValueError as exc:
        return error(str(exc))
    db().run(
        """INSERT INTO profiles (user_id, name, age, sex, height_cm, weight_kg, activity_level,
        dietary_preference, goal, allergies, cuisines, budget_per_day, timeline_weeks, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, age=excluded.age, sex=excluded.sex,
        height_cm=excluded.height_cm, weight_kg=excluded.weight_kg, activity_level=excluded.activity_level,
        dietary_preference=excluded.dietary_preference, goal=excluded.goal, allergies=excluded.allergies,
        cuisines=excluded.cuisines, budget_per_day=excluded.budget_per_day, timeline_weeks=excluded.timeline_weeks,
        updated_at=excluded.updated_at""",
        (
            g.user_id,
            profile["name"],
            profile["age"],
            profile["sex"],
            profile["height_cm"],
            profile["weight_kg"],
            profile["activity_level"],
            profile["dietary_preference"],
            profile["goal"],
            json.dumps(profile["allergies"]),
            json.dumps(profile["cuisines"]),
            profile["budget_per_day"],
            profile["timeline_weeks"],
            now_iso(),
        ),
    )
    return jsonify({"profile": profile})


@api.post("/targets")
@login_required
def targets():
    payload = request.get_json(silent=True) or {}
    profile = payload.get("profile")
    if not profile:
        row = db().one("SELECT * FROM profiles WHERE user_id = ?", (g.user_id,))
        profile = serialize_profile(row)
    if not profile:
        return error("Save your profile before calculating targets.", 400)
    try:
        return jsonify({"targets": compute_targets(profile)})
    except ValueError as exc:
        return error(str(exc))


@api.get("/foods")
@login_required
def foods():
    return jsonify({"foods": [{"id": food["id"], "name": food["name"], "per100": food["per100"], "tags": food["tags"]} for food in FOODS]})


@api.get("/plans")
@login_required
def list_plans():
    rows = db().many("SELECT id, created_at, total_calories, payload FROM plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (g.user_id,))
    plans = []
    for row in rows:
        payload = json.loads(row["payload"])
        payload["id"] = row["id"]
        payload["created_at"] = row["created_at"]
        plans.append(payload)
    return jsonify({"plans": plans})


@api.post("/plans")
@login_required
def create_plan():
    profile_row = db().one("SELECT * FROM profiles WHERE user_id = ?", (g.user_id,))
    profile = serialize_profile(profile_row)
    if not profile:
        return error("Save your profile before generating a plan.")
    payload = request.get_json(silent=True) or {}
    try:
        targets_data = payload.get("targets") or compute_targets(profile)
        plan = generate_plan(profile, targets_data)
    except ValueError as exc:
        return error(str(exc))
    plan_id = uuid.uuid4().hex
    created_at = now_iso()
    plan["id"] = plan_id
    plan["created_at"] = created_at
    db().run(
        "INSERT INTO plans (id, user_id, created_at, total_calories, payload) VALUES (?, ?, ?, ?, ?)",
        (plan_id, g.user_id, created_at, plan["totals"]["kcal"], json.dumps(plan)),
    )
    return jsonify({"plan": plan}), 201


@api.get("/plans/<plan_id>")
@login_required
def get_plan(plan_id: str):
    row = db().one("SELECT payload FROM plans WHERE id = ? AND user_id = ?", (plan_id, g.user_id))
    if not row:
        return error("Plan not found.", 404)
    return jsonify({"plan": json.loads(row["payload"])})


@api.get("/intake")
@login_required
def list_intake():
    entry_date = request.args.get("date", date.today().isoformat())
    rows = db().many("SELECT * FROM intake WHERE user_id = ? AND entry_date = ? ORDER BY created_at DESC", (g.user_id, entry_date))
    totals = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    entries = []
    for row in rows:
        item = {key: row[key] for key in ("id", "entry_date", "food_id", "food_name", "grams", "kcal", "protein", "carbs", "fat", "created_at")}
        entries.append(item)
        for key in totals:
            totals[key] += row[key]
    return jsonify({"date": entry_date, "entries": entries, "totals": {key: round(value, 1) for key, value in totals.items()}})


@api.post("/intake")
@login_required
def add_intake():
    payload = request.get_json(silent=True) or {}
    food = food_by_id(str(payload.get("food_id", "")))
    if not food:
        return error("Choose a food from the catalog.")
    try:
        grams = float(payload.get("grams", 0))
    except (TypeError, ValueError):
        return error("Grams must be a number.")
    if not 1 <= grams <= 1000:
        return error("Grams must be between 1 and 1000.")
    entry_date = str(payload.get("date", date.today().isoformat()))
    try:
        date.fromisoformat(entry_date)
    except ValueError:
        return error("Date must use YYYY-MM-DD.")
    factor = grams / 100
    nutrition = {key: round(value * factor, 1) for key, value in food["per100"].items()}
    entry_id = db().run(
        """INSERT INTO intake (user_id, entry_date, food_id, food_name, grams, kcal, protein, carbs, fat, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (g.user_id, entry_date, food["id"], food["name"], grams, nutrition["kcal"], nutrition["protein"], nutrition["carbs"], nutrition["fat"], now_iso()),
    )
    return jsonify({"entry": {"id": entry_id, "entry_date": entry_date, "food_id": food["id"], "food_name": food["name"], "grams": grams, **nutrition}}), 201


@api.delete("/intake/<int:entry_id>")
@login_required
def delete_intake(entry_id: int):
    deleted = db().run("DELETE FROM intake WHERE id = ? AND user_id = ?", (entry_id, g.user_id))
    if deleted == 0:
        return error("Intake entry not found.", 404)
    return jsonify({"ok": True})


@api.get("/dashboard")
@login_required
def dashboard():
    profile_row = db().one("SELECT * FROM profiles WHERE user_id = ?", (g.user_id,))
    profile = serialize_profile(profile_row)
    targets_data = None
    if profile:
        targets_data = compute_targets(profile)
    current = db().one("SELECT payload FROM plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (g.user_id,))
    intake_response = list_intake().json if False else None
    entry_date = date.today().isoformat()
    intake_rows = db().many("SELECT kcal, protein, carbs, fat FROM intake WHERE user_id = ? AND entry_date = ?", (g.user_id, entry_date))
    intake_totals = {key: round(sum(row[key] for row in intake_rows), 1) for key in ("kcal", "protein", "carbs", "fat")}
    recent = db().many("SELECT id, created_at, total_calories FROM plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (g.user_id,))
    return jsonify({
        "profile": profile,
        "targets": targets_data,
        "current_plan": json.loads(current["payload"]) if current else None,
        "today": {"date": entry_date, "intake": intake_totals},
        "recent_plans": recent,
    })


@api.post("/storage/profile-photo")
@login_required
def upload_profile_photo():
    file_storage = request.files.get("file")
    try:
        stored = current_app.extensions["storage"].save(g.user_id, file_storage)
    except ValueError as exc:
        return error(str(exc))
    upload_id = uuid.uuid4().hex
    db().run(
        "INSERT INTO uploads (id, user_id, object_key, filename, content_type, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (upload_id, g.user_id, stored["object_key"], stored["filename"], stored["content_type"], stored["size_bytes"], now_iso()),
    )
    url = f"/api/storage/{upload_id}"
    db().run("UPDATE profiles SET photo_url = ?, updated_at = ? WHERE user_id = ?", (url, now_iso(), g.user_id))
    return jsonify({"upload": {"id": upload_id, "url": url, **stored}}), 201


@api.get("/storage/<upload_id>")
@login_required
def get_profile_photo(upload_id: str):
    upload = db().one("SELECT * FROM uploads WHERE id = ? AND user_id = ?", (upload_id, g.user_id))
    if not upload:
        return error("Upload not found.", 404)
    try:
        path = current_app.extensions["storage"].path_for(upload["object_key"])
    except ValueError:
        return error("Invalid storage key.", 400)
    if not path.is_file():
        return error("Stored object is unavailable.", 404)
    return send_file(path, mimetype=upload["content_type"], download_name=upload["filename"])
