"""Statistics & Reports: daily summary, weekly report, CSV export."""

import io
import csv
from datetime import date

from services.water import progress_bar, week_chart
from services.mood import calc_trend, MOOD_SCORES
from services.sleep import calc_sleep_avg, sleep_recommendation
from services.headache import format_duration, triggers_from_str, TRIGGER_LABELS


def _today_str(logged_at) -> str:
    dt = logged_at if isinstance(logged_at, str) else str(logged_at)
    return dt[:10]


# --- /today ---

def format_today_summary(
    today: str,
    water_today: int,
    water_goal: int,
    user_row: tuple | None,
    mood_last: tuple | None,
    sleep_last: tuple | None,
    headache_count: int,
) -> str:
    lines = [f"📋 <b>Сводка за сегодня</b> ({today})\n"]

    # Вода
    bar = progress_bar(water_today, water_goal)
    lines.append(f"💧 <b>Вода</b>\n{bar}")

    # Настроение
    if mood_last:
        emoji, note, logged_at = mood_last
        is_today = _today_str(logged_at) == today
        label = f"{emoji}" + (f" — {note}" if note else "")
        suffix = "" if is_today else f" ({_today_str(logged_at)})"
        lines.append(f"😊 <b>Настроение</b>: {label}{suffix}")
    else:
        lines.append("😊 <b>Настроение</b>: не записано")

    # Сон
    if sleep_last:
        sleep_date, hours, quality = sleep_last
        date_str = sleep_date if isinstance(sleep_date, str) else str(sleep_date)
        is_today = date_str == today
        suffix = "" if is_today else f" ({date_str})"
        lines.append(f"😴 <b>Сон</b>: {hours}ч{suffix}")
    else:
        lines.append("😴 <b>Сон</b>: не записан")

    # Мигрень
    if headache_count > 0:
        lines.append(f"🤕 <b>Мигрень</b>: {headache_count} эп.")
    else:
        lines.append("🤕 <b>Мигрень</b>: эпизодов нет")

    # КБЖУ цели (из профиля)
    if user_row and len(user_row) > 14 and user_row[11]:
        cal, prot, fat, carbs = user_row[11], user_row[12], user_row[13], user_row[14]
        lines.append(
            f"\n🍽 <b>Цели КБЖУ</b>: {cal} ккал\n"
            f"  Б {prot}г | Ж {fat}г | У {carbs}г"
        )

    return "\n\n".join(lines)


# --- /week ---

def format_week_report(
    water_week: dict[str, int],
    water_goal: int,
    mood_rows: list,
    sleep_rows: list,
    headache_rows: list,
) -> str:
    lines = ["📊 <b>Отчёт за неделю</b>\n"]

    # Вода
    avg_water = int(sum(water_week.values()) / len(water_week)) if water_week else 0
    chart = week_chart(water_week, water_goal)
    lines.append(f"💧 <b>Вода</b>\n{chart}\nСреднее: <b>{avg_water} мл/день</b>")

    # Настроение
    if mood_rows:
        trend = calc_trend(mood_rows)
        trend_icon = {"улучшается": "📈", "ухудшается": "📉", "стабильно": "➡️"}[trend]
        recent = " ".join(r[0] for r in mood_rows[:7])
        lines.append(f"😊 <b>Настроение</b>\n{recent}\n{trend_icon} Тренд: <b>{trend}</b>")
    else:
        lines.append("😊 <b>Настроение</b>: нет записей")

    # Сон
    if sleep_rows:
        avg_sleep = calc_sleep_avg(sleep_rows)
        rec = sleep_recommendation(avg_sleep)
        lines.append(f"😴 <b>Сон</b>\nСреднее: <b>{avg_sleep}ч</b>\n💡 {rec}")
    else:
        lines.append("😴 <b>Сон</b>: нет записей")

    # Мигрень
    if headache_rows:
        count = len(headache_rows)
        avg_int = round(sum(r[0] for r in headache_rows) / count, 1)
        lines.append(
            f"🤕 <b>Мигрень</b>\nЭпизодов: <b>{count}</b> | "
            f"Средняя интенсивность: <b>{avg_int}/10</b>"
        )
    else:
        lines.append("🤕 <b>Мигрень</b>: эпизодов нет")

    return "\n\n".join(lines)


# --- /export CSV ---

def build_csv(
    water_rows: list,
    mood_rows: list,
    sleep_rows: list,
    headache_rows: list,
) -> bytes:
    """Формирует CSV-файл со всеми данными пользователя."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["=== WATER LOG ==="])
    writer.writerow(["amount_ml", "logged_at"])
    for row in water_rows:
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(["=== MOOD LOG ==="])
    writer.writerow(["emoji", "note", "logged_at"])
    for row in mood_rows:
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(["=== SLEEP LOG ==="])
    writer.writerow(["sleep_date", "hours", "quality"])
    for row in sleep_rows:
        writer.writerow(row)

    writer.writerow([])
    writer.writerow(["=== HEADACHE LOG ==="])
    writer.writerow(["intensity", "location", "triggers", "duration_min", "logged_at"])
    for row in headache_rows:
        # Декодируем триггеры в читаемый вид
        triggers_str = ", ".join(
            TRIGGER_LABELS.get(k, k) for k in triggers_from_str(row[2])
        ) if row[2] else ""
        writer.writerow([row[0], row[1] or "", triggers_str,
                         format_duration(row[3]), row[4]])

    return buf.getvalue().encode("utf-8-sig")  # BOM для Excel
