"""APScheduler: water reminders + evening check-in."""

import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from db.database import db

logger = logging.getLogger(__name__)

_TZ = settings.TIMEZONE  # "Europe/Belgrade"


# --- Тексты напоминаний ---

def water_reminder_text(water_today: int, goal: int) -> str:
    remaining = max(0, goal - water_today)
    pct = int(water_today / goal * 100) if goal > 0 else 0
    if pct == 0:
        return (
            f"💧 Вы ещё не пили воду сегодня!\n"
            f"Цель: {goal} мл. Не забывайте пить воду 🌊"
        )
    return (
        f"💧 Напоминание о воде\n\n"
        f"Выпито: {water_today} мл ({pct}%)\n"
        f"Осталось до цели: {remaining} мл\n\n"
        f"Выпейте стакан воды прямо сейчас! 🥤"
    )


def evening_checkin_text(has_mood: bool, has_sleep: bool, water_pct: int) -> str:
    missing = []
    if not has_mood:
        missing.append("😊 настроение")
    if not has_sleep:
        missing.append("😴 сон")
    if water_pct < 80:
        missing.append(f"💧 вода ({water_pct}%)")

    if not missing:
        return "🌙 Отличный день! Все показатели записаны. Спокойной ночи! 😴"

    items = ", ".join(missing)
    return (
        f"🌙 Вечерний чекин\n\n"
        f"Как прошёл день? Не забыли записать:\n{items}\n\n"
        f"Займёт меньше минуты 👇"
    )


def _evening_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="😊 Настроение", callback_data="mood_checkin")
    builder.button(text="😴 Сон", callback_data="sleep_checkin")
    builder.button(text="💧 Вода", callback_data="water_checkin")
    builder.adjust(3)
    return builder.as_markup()


# --- Задачи планировщика ---

async def job_water_reminder(bot) -> None:
    """Каждые 2 часа (10-20ч): напомнить тем, кто не дотягивает до цели."""
    today = date.today().isoformat()
    now_hour = datetime.now().hour
    users = await db.get_all_users()

    sent = 0
    for user_row in users:
        user_id = user_row[0]
        try:
            water_today = await db.get_water_today(user_id, today)
            goal = await db.get_water_goal(user_id) or 2000

            # После 14:00 — напоминаем только тем, кто выпил < 50%
            if now_hour >= 14 and water_today >= goal * 0.5:
                continue

            await bot.send_message(user_id, water_reminder_text(water_today, goal))
            sent += 1
        except Exception:
            pass  # бот заблокирован, пользователь не найден и т.д.

    logger.info(f"Water reminder: sent to {sent}/{len(users)} users")


async def job_evening_checkin(bot) -> None:
    """21:00: вечерний чекин — что не записано за день."""
    today = date.today().isoformat()
    users = await db.get_all_users()

    sent = 0
    for user_row in users:
        user_id = user_row[0]
        try:
            water_today = await db.get_water_today(user_id, today)
            goal = await db.get_water_goal(user_id) or 2000
            water_pct = int(water_today / goal * 100) if goal > 0 else 0

            mood_rows = await db.get_mood_history(user_id, limit=1)
            sleep_rows = await db.get_sleep_history(user_id, limit=1)

            has_mood = bool(mood_rows and mood_rows[0][2][:10] == today)
            has_sleep = bool(sleep_rows and str(sleep_rows[0][0])[:10] == today)

            text = evening_checkin_text(has_mood, has_sleep, water_pct)
            await bot.send_message(user_id, text, reply_markup=_evening_keyboard())
            sent += 1
        except Exception:
            pass

    logger.info(f"Evening check-in: sent to {sent}/{len(users)} users")


# --- Настройка планировщика ---

def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=_TZ)

    # Вода: каждые 2 часа с 10:00 до 20:00
    scheduler.add_job(
        job_water_reminder,
        CronTrigger(hour="10,12,14,16,18,20", minute=0, timezone=_TZ),
        args=[bot],
        id="water_reminder",
        replace_existing=True,
    )

    # Вечерний чекин: 21:00
    scheduler.add_job(
        job_evening_checkin,
        CronTrigger(hour=21, minute=0, timezone=_TZ),
        args=[bot],
        id="evening_checkin",
        replace_existing=True,
    )

    return scheduler
