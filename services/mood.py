"""Mood tracking helpers: emoji grid, trend analysis, statistics."""

MOOD_EMOJIS = ["😄", "😊", "🙂", "😐", "😔", "😢", "😡", "😴"]

# Числовая оценка для расчёта тренда (выше = лучше настроение)
MOOD_SCORES: dict[str, int] = {
    "😄": 8, "😊": 7, "🙂": 6, "😐": 5,
    "😔": 4, "😢": 3, "😡": 2, "😴": 1,
}


def calc_trend(rows: list) -> str:
    """Тренд по последним 6 записям: улучшается / ухудшается / стабильно.

    rows — список (emoji, note, logged_at), отсортированный DESC (новые первые).
    """
    if len(rows) < 2:
        return "стабильно"
    scores = [MOOD_SCORES.get(r[0], 0) for r in rows]
    half = len(scores) // 2
    recent_avg = sum(scores[:half]) / half
    older_avg = sum(scores[half:]) / (len(scores) - half)
    delta = recent_avg - older_avg
    if delta >= 0.5:
        return "улучшается"
    if delta <= -0.5:
        return "ухудшается"
    return "стабильно"


def mood_stats(rows: list) -> dict[str, int]:
    """Счётчик каждого эмодзи: {'😊': 3, ...}"""
    counts: dict[str, int] = {}
    for row in rows:
        emoji = row[0]
        counts[emoji] = counts.get(emoji, 0) + 1
    return counts


def format_mood_history(rows: list) -> str:
    """Форматирует историю настроений + тренд + статистику."""
    if not rows:
        return "😊 <b>Настроение</b>\n\nЗаписей ещё нет."

    trend = calc_trend(rows)
    trend_icon = {"улучшается": "📈", "ухудшается": "📉", "стабильно": "➡️"}[trend]
    stats = mood_stats(rows)

    # Последние записи
    lines = []
    for emoji, note, logged_at in rows:
        # logged_at может быть datetime-объектом (PG) или строкой (SQLite)
        dt_str = logged_at if isinstance(logged_at, str) else str(logged_at)
        date_part = dt_str[:10]  # YYYY-MM-DD
        note_part = f" — {note}" if note else ""
        lines.append(f"{date_part} {emoji}{note_part}")

    stats_line = " ".join(f"{e}×{c}" for e, c in sorted(stats.items(), key=lambda x: -x[1]))

    return (
        f"😊 <b>Настроение</b>\n\n"
        f"<b>Последние записи:</b>\n"
        + "\n".join(lines)
        + f"\n\n{trend_icon} Тренд: <b>{trend}</b>\n"
        f"📊 Статистика: {stats_line}"
    )
