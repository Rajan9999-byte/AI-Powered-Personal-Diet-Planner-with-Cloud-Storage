from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Any


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

FOODS: list[dict[str, Any]] = [
    {"id": "oats", "name": "Rolled oats", "meal": "breakfast", "per100": {"kcal": 379, "protein": 13.2, "carbs": 67.7, "fat": 6.5}, "tags": ["vegan", "vegetarian"], "allergens": ["gluten"]},
    {"id": "banana", "name": "Banana", "meal": "breakfast", "per100": {"kcal": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "greek_yogurt", "name": "Greek yogurt", "meal": "breakfast", "per100": {"kcal": 97, "protein": 9.0, "carbs": 3.8, "fat": 5.0}, "tags": ["vegetarian"], "allergens": ["lactose"]},
    {"id": "egg", "name": "Egg", "meal": "breakfast", "per100": {"kcal": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0}, "tags": ["nonveg"], "allergens": ["egg"]},
    {"id": "tofu", "name": "Herbed tofu", "meal": "lunch", "per100": {"kcal": 144, "protein": 17.0, "carbs": 3.0, "fat": 8.0}, "tags": ["vegan", "vegetarian"], "allergens": ["soy"]},
    {"id": "lentils", "name": "Lentil dal", "meal": "lunch", "per100": {"kcal": 116, "protein": 9.0, "carbs": 20.0, "fat": 0.4}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "brown_rice", "name": "Brown rice", "meal": "lunch", "per100": {"kcal": 123, "protein": 2.7, "carbs": 25.6, "fat": 1.0}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "chicken", "name": "Grilled chicken", "meal": "lunch", "per100": {"kcal": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6}, "tags": ["nonveg"], "allergens": []},
    {"id": "apple", "name": "Apple", "meal": "snack", "per100": {"kcal": 52, "protein": 0.3, "carbs": 14.0, "fat": 0.2}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "almonds", "name": "Almonds", "meal": "snack", "per100": {"kcal": 579, "protein": 21.2, "carbs": 21.6, "fat": 49.9}, "tags": ["vegan", "vegetarian"], "allergens": ["nuts"]},
    {"id": "berries", "name": "Mixed berries", "meal": "snack", "per100": {"kcal": 57, "protein": 0.7, "carbs": 14.0, "fat": 0.3}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "hummus", "name": "Hummus", "meal": "snack", "per100": {"kcal": 166, "protein": 7.9, "carbs": 14.3, "fat": 9.6}, "tags": ["vegan", "vegetarian"], "allergens": ["sesame"]},
    {"id": "quinoa", "name": "Quinoa", "meal": "dinner", "per100": {"kcal": 120, "protein": 4.4, "carbs": 21.3, "fat": 1.9}, "tags": ["vegan", "vegetarian"], "allergens": []},
    {"id": "salmon", "name": "Baked salmon", "meal": "dinner", "per100": {"kcal": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0}, "tags": ["nonveg"], "allergens": ["fish"]},
    {"id": "vegetables", "name": "Roasted vegetables", "meal": "dinner", "per100": {"kcal": 65, "protein": 2.0, "carbs": 10.0, "fat": 2.0}, "tags": ["vegan", "vegetarian"], "allergens": []},
]

MEAL_LABELS = {"breakfast": "Breakfast", "lunch": "Lunch", "snack": "Snack", "dinner": "Dinner"}
MEAL_SHARES = {"breakfast": 0.25, "lunch": 0.30, "snack": 0.15, "dinner": 0.30}


def _number(value: Any, label: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a number.") from error
    if not minimum <= number <= maximum:
        raise ValueError(f"{label} must be between {minimum:g} and {maximum:g}.")
    return number


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "name": str(profile.get("name", "")).strip(),
        "age": int(_number(profile.get("age"), "Age", 13, 100)),
        "sex": str(profile.get("sex", "female")).lower(),
        "height_cm": _number(profile.get("height_cm"), "Height", 100, 230),
        "weight_kg": _number(profile.get("weight_kg"), "Weight", 30, 250),
        "activity_level": str(profile.get("activity_level", "moderate")).lower(),
        "dietary_preference": str(profile.get("dietary_preference", "vegetarian")).lower(),
        "goal": str(profile.get("goal", "maintain")).lower(),
        "allergies": [str(item).lower().strip() for item in profile.get("allergies", []) if str(item).strip()],
        "cuisines": [str(item).strip() for item in profile.get("cuisines", []) if str(item).strip()],
        "budget_per_day": float(profile["budget_per_day"]) if profile.get("budget_per_day") not in (None, "") else None,
        "timeline_weeks": int(profile["timeline_weeks"]) if profile.get("timeline_weeks") not in (None, "") else None,
    }
    if not normalized["name"]:
        raise ValueError("Name is required.")
    if normalized["sex"] not in {"female", "male", "other"}:
        raise ValueError("Sex must be female, male, or other.")
    if normalized["activity_level"] not in ACTIVITY_MULTIPLIERS:
        raise ValueError("Choose a supported activity level.")
    if normalized["dietary_preference"] not in {"vegan", "vegetarian", "nonveg"}:
        raise ValueError("Choose vegan, vegetarian, or non-vegetarian.")
    if normalized["goal"] not in {"balanced", "cut", "gain", "maintain", "fitness"}:
        raise ValueError("Choose a supported goal.")
    if normalized["budget_per_day"] is not None and not 0 <= normalized["budget_per_day"] <= 1000:
        raise ValueError("Budget must be between 0 and 1000.")
    if normalized["timeline_weeks"] is not None and not 1 <= normalized["timeline_weeks"] <= 104:
        raise ValueError("Timeline must be between 1 and 104 weeks.")
    return normalized


def compute_targets(profile: dict[str, Any]) -> dict[str, Any]:
    profile = validate_profile(profile)
    sex_offset = 5 if profile["sex"] == "male" else -161
    bmr = (10 * profile["weight_kg"]) + (6.25 * profile["height_cm"]) - (5 * profile["age"]) + sex_offset
    tdee = bmr * ACTIVITY_MULTIPLIERS[profile["activity_level"]]
    goal_delta = {"cut": -0.15, "gain": 0.15, "fitness": 0.05}.get(profile["goal"], 0)
    calories = round(tdee * (1 + goal_delta))
    macros = {
        "protein": round((calories * 0.30) / 4),
        "carbs": round((calories * 0.40) / 4),
        "fat": round((calories * 0.30) / 9),
    }
    return {"bmr": round(bmr), "tdee": round(tdee), "calories": calories, "macros": macros}


def compatible_foods(profile: dict[str, Any], meal: str) -> list[dict[str, Any]]:
    preference = profile["dietary_preference"]
    allergies = set(profile.get("allergies", []))
    results = []
    for food in FOODS:
        if food["meal"] != meal or preference not in food["tags"]:
            continue
        if allergies.intersection(food["allergens"]):
            continue
        results.append(deepcopy(food))
    return results


def _nutrition(food: dict[str, Any], grams: float) -> dict[str, float]:
    factor = grams / 100
    return {key: round(value * factor, 1) for key, value in food["per100"].items()}


def generate_plan(profile: dict[str, Any], targets: dict[str, Any]) -> dict[str, Any]:
    profile = validate_profile(profile)
    meals = []
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for meal_id, share in MEAL_SHARES.items():
        candidates = compatible_foods(profile, meal_id)
        if not candidates:
            continue
        meal_target = targets["calories"] * share
        base_grams = [100, 80] if len(candidates) > 1 else [120]
        base_calories = sum(food["per100"]["kcal"] * grams / 100 for food, grams in zip(candidates[:2], base_grams))
        scale = meal_target / max(base_calories, 1)
        items = []
        meal_totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for food, grams in zip(candidates[:2], base_grams):
            portion = max(40, min(400, round((grams * scale) / 5) * 5))
            nutrition = _nutrition(food, portion)
            item = {"food_id": food["id"], "name": food["name"], "grams": portion, **nutrition}
            items.append(item)
            for key in meal_totals:
                meal_totals[key] += nutrition[key]
                totals[key] += nutrition[key]
        meals.append({"id": meal_id, "label": MEAL_LABELS[meal_id], "target_calories": round(meal_target), "items": items, "totals": {key: round(value) for key, value in meal_totals.items()}})

    return {
        "title": "A balanced day built around your profile",
        "source": "rule_based_fallback",
        "disclaimer": "Educational wellness example only — not medical or clinical nutrition advice.",
        "created_for": {"dietary_preference": profile["dietary_preference"], "goal": profile["goal"]},
        "targets": targets,
        "meals": meals,
        "totals": {key: round(value) for key, value in totals.items()},
        "hydration": "A gentle reminder: keep water nearby and adjust intake for your climate and activity.",
    }


def food_by_id(food_id: str) -> dict[str, Any] | None:
    for food in FOODS:
        if food["id"] == food_id:
            return deepcopy(food)
    return None
