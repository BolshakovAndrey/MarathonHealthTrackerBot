"""KBJU calculator service (Mifflin-St Jeor)."""

from dataclasses import dataclass


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "very_high": 1.9,
}

GOAL_CALORIE_FACTOR = {
    "lose": 0.8,      # -20%
    "maintain": 1.0,  # 0%
    "gain": 1.15,     # +15%
}

# Calories share by goal (protein/fat/carbs). Must sum to 1.0.
GOAL_BJU_SPLIT = {
    "lose": (0.30, 0.30, 0.40),
    "maintain": (0.30, 0.25, 0.45),
    "gain": (0.25, 0.25, 0.50),
}


@dataclass(frozen=True)
class KBJUResult:
    bmr: float
    tdee: float
    calories: int
    protein: int
    fat: int
    carbs: int


def calculate_bmr(gender: str, age: int, height_cm: float, weight_kg: float) -> float:
    """
    Mifflin-St Jeor:
      male:   10*w + 6.25*h - 5*a + 5
      female: 10*w + 6.25*h - 5*a - 161
    """
    g = (gender or "").strip().lower()
    if g not in {"male", "female"}:
        raise ValueError("gender must be 'male' or 'female'")
    if age <= 0 or height_cm <= 0 or weight_kg <= 0:
        raise ValueError("age/height/weight must be positive")

    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + (5 if g == "male" else -161), 2)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    activity = (activity_level or "").strip().lower()
    if activity not in ACTIVITY_FACTORS:
        raise ValueError(f"unknown activity_level: {activity_level}")
    if bmr <= 0:
        raise ValueError("bmr must be positive")
    return round(bmr * ACTIVITY_FACTORS[activity], 2)


def calculate_bju(calories: int, goal: str) -> tuple[int, int, int]:
    """
    Converts calories -> grams by goal split:
      protein/carbs: 4 kcal/g
      fat: 9 kcal/g
    """
    g = (goal or "").strip().lower()
    if g not in GOAL_BJU_SPLIT:
        raise ValueError(f"unknown goal: {goal}")
    if calories <= 0:
        raise ValueError("calories must be positive")

    p_share, f_share, c_share = GOAL_BJU_SPLIT[g]
    protein = int(round((calories * p_share) / 4))
    fat = int(round((calories * f_share) / 9))
    carbs = int(round((calories * c_share) / 4))
    return protein, fat, carbs


def calculate_kbju(
    gender: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
) -> KBJUResult:
    bmr = calculate_bmr(gender=gender, age=age, height_cm=height_cm, weight_kg=weight_kg)
    tdee = calculate_tdee(bmr=bmr, activity_level=activity_level)

    g = (goal or "").strip().lower()
    if g not in GOAL_CALORIE_FACTOR:
        raise ValueError(f"unknown goal: {goal}")
    calories = int(round(tdee * GOAL_CALORIE_FACTOR[g]))
    protein, fat, carbs = calculate_bju(calories=calories, goal=g)
    return KBJUResult(
        bmr=bmr,
        tdee=tdee,
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs,
    )
