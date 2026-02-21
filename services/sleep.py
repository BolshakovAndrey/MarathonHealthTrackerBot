"""Sleep tracking helpers: stats, recommendation, weekly chart."""

SLEEP_NORM_MIN = 7.0
SLEEP_NORM_MAX = 9.0

QUALITY_LABELS = {3: "отлично", 2: "хорошо", 1: "плохо"}
QUALITY_FROM_LABEL = {v: k for k, v in QUALITY_LABELS.items()}


def calc_sleep_avg(rows: list) -> float:
    """Средние часы сна. rows — (sleep_date, hours, quality)."""
    if not rows:
        return 0.0
    return round(sum(r[1] for r in rows) / len(rows), 1)


def sleep_recommendation(avg_hours: float) -> str:
    """Рекомендация на основе среднего значения."""
    if avg_hours == 0:
        return "Начните вести трекинг сна — норма 7–9 часов."
    if avg_hours < SLEEP_NORM_MIN:
        deficit = round(SLEEP_NORM_MIN - avg_hours, 1)
        return f"Недосып: среднее {avg_hours}ч. Добавьте {deficit}ч до нормы."
    if avg_hours > SLEEP_NORM_MAX:
        excess = round(avg_hours - SLEEP_NORM_MAX, 1)
        return f"Пересып: среднее {avg_hours}ч. Норма до {SLEEP_NORM_MAX}ч (+{excess}ч)."
    return f"Отлично! Среднее {avg_hours}ч — в пределах нормы."


def sleep_chart(rows: list) -> str:
    """Мини-график за записанные дни."""
    lines = []
    for sleep_date, hours, quality in rows:
        date_str = sleep_date if isinstance(sleep_date, str) else str(sleep_date)
        day = date_str[5:]  # MM-DD
        quality_icon = QUALITY_LABELS.get(quality, "—") if quality else "—"
        if hours >= SLEEP_NORM_MIN:
            icon = "🌙"
        elif hours >= 5:
            icon = "🌛"
        else:
            icon = "😵"
        lines.append(f"{day} {icon} {hours}ч [{quality_icon}]")
    return "\n".join(lines) if lines else "Записей нет."


def format_sleep_status(rows: list) -> str:
    avg = calc_sleep_avg(rows)
    rec = sleep_recommendation(avg)
    chart = sleep_chart(rows)
    return (
        f"😴 <b>Сон</b>\n\n"
        f"<b>Последние записи:</b>\n{chart}\n\n"
        f"💡 {rec}"
    )
