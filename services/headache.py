"""Headache tracking: constants, formatting, analytics."""

from collections import Counter

LOCATIONS = [
    ("whole", "Вся голова"),
    ("temples", "Виски"),
    ("forehead", "Лоб"),
    ("occiput", "Затылок"),
    ("one_side", "Одна сторона"),
]
LOCATION_LABELS = {k: v for k, v in LOCATIONS}

TRIGGERS = [
    ("stress", "Стресс"),
    ("sleep", "Недосып"),
    ("food", "Еда"),
    ("weather", "Погода"),
    ("screens", "Экраны"),
    ("other", "Другое"),
]
TRIGGER_LABELS = {k: v for k, v in TRIGGERS}

DURATIONS = [
    (15, "15 мин"),
    (30, "30 мин"),
    (60, "1 час"),
    (120, "2 часа"),
    (240, "4 часа"),
    (480, "8+ часов"),
]


def triggers_to_str(selected: list[str]) -> str | None:
    """Список ключей → строка для хранения в БД."""
    return ",".join(selected) if selected else None


def triggers_from_str(value: str | None) -> list[str]:
    """Строка из БД → список ключей."""
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def format_duration(minutes: int | None) -> str:
    if not minutes:
        return "—"
    if minutes < 60:
        return f"{minutes} мин"
    hours = minutes / 60
    return f"{hours:.0f}ч" if hours == int(hours) else f"{hours:.1f}ч"


def format_headache_entry(row: tuple) -> str:
    """(intensity, location, triggers, duration, logged_at) → строка."""
    intensity, location, triggers_raw, duration, logged_at = row
    dt_str = logged_at if isinstance(logged_at, str) else str(logged_at)
    date_part = dt_str[:10]

    loc_label = LOCATION_LABELS.get(location or "", location or "—")
    trigger_keys = triggers_from_str(triggers_raw)
    trigger_text = ", ".join(TRIGGER_LABELS.get(k, k) for k in trigger_keys) or "—"
    dur_text = format_duration(duration)

    pain_icon = "🔴" if intensity >= 8 else "🟠" if intensity >= 5 else "🟡"
    return (
        f"{date_part} {pain_icon} интенсивность {intensity}/10\n"
        f"  📍 {loc_label} | ⏱ {dur_text}\n"
        f"  ⚡ {trigger_text}"
    )


def headache_analytics(rows: list) -> str:
    """Аналитика по истории: частота, триггеры, интенсивность."""
    if not rows:
        return "Эпизодов ещё нет."

    total = len(rows)
    avg_intensity = round(sum(r[0] for r in rows) / total, 1)

    all_triggers: list[str] = []
    for row in rows:
        all_triggers.extend(triggers_from_str(row[2]))
    top_triggers = Counter(all_triggers).most_common(3)

    trigger_line = ", ".join(
        f"{TRIGGER_LABELS.get(k, k)} ({c}×)" for k, c in top_triggers
    ) or "нет данных"

    locations = [r[1] for r in rows if r[1]]
    top_loc = Counter(locations).most_common(1)
    loc_line = LOCATION_LABELS.get(top_loc[0][0], top_loc[0][0]) if top_loc else "—"

    return (
        f"📊 <b>Аналитика</b>\n\n"
        f"Эпизодов: <b>{total}</b>\n"
        f"Средняя интенсивность: <b>{avg_intensity}/10</b>\n"
        f"Частая локализация: <b>{loc_line}</b>\n"
        f"Топ триггеры: {trigger_line}"
    )


def format_headache_status(rows: list) -> str:
    if not rows:
        return (
            "🤕 <b>Мигрень / Головная боль</b>\n\n"
            "Записей ещё нет.\n\n"
            "Нажмите <b>Записать эпизод</b>, чтобы начать трекинг."
        )
    entries = "\n\n".join(format_headache_entry(r) for r in rows[:5])
    analytics = headache_analytics(rows)
    return (
        f"🤕 <b>Мигрень / Головная боль</b>\n\n"
        f"<b>Последние эпизоды:</b>\n{entries}\n\n"
        f"{analytics}"
    )
