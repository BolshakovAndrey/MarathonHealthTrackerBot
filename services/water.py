"""Water tracking helpers: goal calculation, progress bar, weekly stats."""

from datetime import date, timedelta

BLOCKS = 8
FILLED = "🟦"
EMPTY = "⬜"

# Дефолты если профиль не заполнен
DEFAULT_GOAL_FEMALE_ML = 2500
DEFAULT_GOAL_MALE_ML = 3500
WEIGHT_FACTOR_ML = 30  # мл на кг веса


def calc_default_goal(gender: str | None, weight_kg: float | None) -> int:
    """Цель по полу и весу. Диапазон [1500, 4000] мл."""
    if weight_kg and weight_kg > 0:
        goal = int(weight_kg * WEIGHT_FACTOR_ML)
    elif gender == "female":
        goal = DEFAULT_GOAL_FEMALE_ML
    else:
        goal = DEFAULT_GOAL_MALE_ML
    return max(1500, min(4000, goal))


def progress_bar(current_ml: int, goal_ml: int) -> str:
    """🟦🟦🟦⬜⬜⬜⬜⬜ 375/2000 мл (19%)"""
    if goal_ml <= 0:
        return f"{EMPTY * BLOCKS} {current_ml} мл"
    ratio = min(current_ml / goal_ml, 1.0)
    filled = round(ratio * BLOCKS)
    bar = FILLED * filled + EMPTY * (BLOCKS - filled)
    pct = int(ratio * 100)
    return f"{bar} {current_ml}/{goal_ml} мл ({pct}%)"


def week_dates(today: date | None = None) -> list[str]:
    """Последние 7 дней включая сегодня, от старых к новым."""
    if today is None:
        today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]


def week_chart(totals: dict[str, int], goal_ml: int) -> str:
    """Мини-график за 7 дней."""
    lines = []
    for date_str, amount in totals.items():
        day = date_str[5:]  # MM-DD
        ratio = amount / goal_ml if goal_ml > 0 else 0
        if ratio >= 1.0:
            icon = "💧"
        elif ratio >= 0.5:
            icon = "🔹"
        else:
            icon = "▫️"
        lines.append(f"{day} {icon} {amount} мл")
    return "\n".join(lines)


def format_water_status(current_ml: int, goal_ml: int, week: dict[str, int]) -> str:
    bar = progress_bar(current_ml, goal_ml)
    avg = int(sum(week.values()) / len(week)) if week else 0
    chart = week_chart(week, goal_ml)
    return (
        f"💧 <b>Вода сегодня</b>\n\n"
        f"{bar}\n\n"
        f"📅 <b>За 7 дней</b>\n{chart}\n\n"
        f"Среднее за неделю: <b>{avg} мл</b>"
    )
