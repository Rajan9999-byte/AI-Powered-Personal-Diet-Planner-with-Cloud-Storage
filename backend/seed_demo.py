from __future__ import annotations

import json
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from . import create_app
from .planner import compute_targets, generate_plan


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def seed():
    app = create_app()
    database = app.extensions["db"]
    user = database.one("SELECT * FROM users WHERE email = ?", ("demo@dietly.local",))
    if user:
        user_id = user["id"]
    else:
        user_id = "demo-user"
        database.run(
            "INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, "demo@dietly.local", generate_password_hash("demo12345"), "Demo Planner", now_iso()),
        )
    profile = {
        "name": "Demo Planner", "age": 24, "sex": "female", "height_cm": 165,
        "weight_kg": 62, "activity_level": "moderate", "dietary_preference": "vegetarian",
        "goal": "balanced", "allergies": ["nuts"], "cuisines": ["Indian", "Mediterranean"],
        "budget_per_day": 350, "timeline_weeks": 8,
    }
    database.run(
        """INSERT INTO profiles (user_id, name, age, sex, height_cm, weight_kg, activity_level,
        dietary_preference, goal, allergies, cuisines, budget_per_day, timeline_weeks, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, age=excluded.age, sex=excluded.sex,
        height_cm=excluded.height_cm, weight_kg=excluded.weight_kg, activity_level=excluded.activity_level,
        dietary_preference=excluded.dietary_preference, goal=excluded.goal, allergies=excluded.allergies,
        cuisines=excluded.cuisines, budget_per_day=excluded.budget_per_day, timeline_weeks=excluded.timeline_weeks,
        updated_at=excluded.updated_at""",
        (user_id, profile["name"], profile["age"], profile["sex"], profile["height_cm"], profile["weight_kg"], profile["activity_level"], profile["dietary_preference"], profile["goal"], json.dumps(profile["allergies"]), json.dumps(profile["cuisines"]), profile["budget_per_day"], profile["timeline_weeks"], now_iso()),
    )
    targets = compute_targets(profile)
    plan = generate_plan(profile, targets)
    existing = database.one("SELECT id FROM plans WHERE user_id = ? LIMIT 1", (user_id,))
    if not existing:
        created = now_iso()
        database.run("INSERT INTO plans (id, user_id, created_at, total_calories, payload) VALUES (?, ?, ?, ?, ?)", ("demo-plan", user_id, created, plan["totals"]["kcal"], json.dumps({**plan, "id": "demo-plan", "created_at": created})))
    has_intake = database.one("SELECT id FROM intake WHERE user_id = ? LIMIT 1", (user_id,))
    if not has_intake:
        database.run("INSERT INTO intake (user_id, entry_date, food_id, food_name, grams, kcal, protein, carbs, fat, created_at) VALUES (?, date('now'), 'oats', 'Rolled oats', 60, 227.4, 7.9, 40.6, 3.9, ?)", (user_id, now_iso()))
        database.run("INSERT INTO intake (user_id, entry_date, food_id, food_name, grams, kcal, protein, carbs, fat, created_at) VALUES (?, date('now'), 'apple', 'Apple', 150, 78, 0.5, 21, 0.3, ?)", (user_id, now_iso()))
    print("Seeded demo account: demo@dietly.local / demo12345")


if __name__ == "__main__":
    seed()
