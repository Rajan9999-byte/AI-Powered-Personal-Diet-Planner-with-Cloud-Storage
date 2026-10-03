import pytest

from backend.planner import compatible_foods, compute_targets, generate_plan


BASE_PROFILE = {
    "name": "Test User", "age": 24, "sex": "female", "height_cm": 165,
    "weight_kg": 62, "activity_level": "moderate", "dietary_preference": "vegetarian",
    "goal": "balanced", "allergies": [], "cuisines": [], "budget_per_day": None,
    "timeline_weeks": None,
}


def test_compute_targets_uses_mifflin_and_activity():
    targets = compute_targets(BASE_PROFILE)
    assert targets["bmr"] == 1370
    assert targets["tdee"] == 2124
    assert targets["calories"] == 2124
    assert targets["macros"]["protein"] == 159


def test_goal_adjustment_changes_calories():
    cut = compute_targets({**BASE_PROFILE, "goal": "cut"})
    gain = compute_targets({**BASE_PROFILE, "goal": "gain"})
    assert cut["calories"] < compute_targets(BASE_PROFILE)["calories"] < gain["calories"]


def test_vegan_and_allergen_filters_exclude_incompatible_foods():
    foods = compatible_foods({**BASE_PROFILE, "dietary_preference": "vegan", "allergies": ["gluten"]}, "breakfast")
    assert foods
    assert all("vegan" in food["tags"] for food in foods)
    assert all("gluten" not in food["allergens"] for food in foods)


def test_plan_has_meals_and_wellness_disclaimer():
    plan = generate_plan(BASE_PROFILE, compute_targets(BASE_PROFILE))
    assert len(plan["meals"]) == 4
    assert plan["source"] == "rule_based_fallback"
    assert "not medical" in plan["disclaimer"]
    assert plan["totals"]["kcal"] > 0
    assert all(40 <= item["grams"] <= 400 for meal in plan["meals"] for item in meal["items"])


def test_invalid_profile_is_rejected():
    with pytest.raises(ValueError, match="Age"):
        compute_targets({**BASE_PROFILE, "age": 4})
