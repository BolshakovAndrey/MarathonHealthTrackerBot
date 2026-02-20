import pytest

from services.kbju import (
    ACTIVITY_FACTORS,
    GOAL_CALORIE_FACTOR,
    calculate_bmr,
    calculate_tdee,
    calculate_bju,
    calculate_kbju,
)


def test_calculate_bmr_male():
    # 10*80 + 6.25*180 - 5*30 + 5 = 1780
    assert calculate_bmr("male", 30, 180, 80) == 1780.0


def test_calculate_bmr_female():
    # 10*60 + 6.25*165 - 5*28 - 161 = 1330.25
    assert calculate_bmr("female", 28, 165, 60) == 1330.25


def test_calculate_tdee():
    bmr = 1600
    assert calculate_tdee(bmr, "moderate") == round(bmr * ACTIVITY_FACTORS["moderate"], 2)


def test_calculate_bju_maintain():
    protein, fat, carbs = calculate_bju(2000, "maintain")
    assert protein == int(round((2000 * 0.30) / 4))
    assert fat == int(round((2000 * 0.25) / 9))
    assert carbs == int(round((2000 * 0.45) / 4))


def test_calculate_kbju_goal_factor_lose():
    result = calculate_kbju(
        gender="male",
        age=35,
        height_cm=175,
        weight_kg=85,
        activity_level="light",
        goal="lose",
    )
    expected_cal = int(round(result.tdee * GOAL_CALORIE_FACTOR["lose"]))
    assert result.calories == expected_cal


@pytest.mark.parametrize(
    "func,args",
    [
        (calculate_bmr, ("other", 30, 180, 80)),
        (calculate_tdee, (1600, "unknown")),
        (calculate_bju, (2000, "unknown")),
        (calculate_kbju, ("male", 30, 180, 80, "moderate", "unknown")),
    ],
)
def test_invalid_inputs_raise(func, args):
    with pytest.raises(ValueError):
        func(*args)


def test_bmr_negative_weight():
    with pytest.raises(ValueError, match="must be positive"):
        calculate_bmr("male", 30, 175.0, -5.0)


def test_tdee_zero_bmr():
    with pytest.raises(ValueError, match="bmr must be positive"):
        calculate_tdee(0.0, "moderate")


def test_bju_zero_calories():
    with pytest.raises(ValueError, match="calories must be positive"):
        calculate_bju(0, "maintain")
