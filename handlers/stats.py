from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from db.database import db
from services.stats import build_csv, format_today_summary, format_week_report
from services.water import week_dates

router = Router()


async def _ensure_user(message: Message):
    user = message.from_user
    await db.upsert_user(user.id, user.username or "", user.full_name or "")


@router.message(Command("today"))
@router.message(F.text == "📊 Статистика")
async def cmd_today(message: Message):
    await _ensure_user(message)
    user_id = message.from_user.id
    today = date.today().isoformat()

    water_today = await db.get_water_today(user_id, today)
    water_goal_row = await db.get_water_goal(user_id)
    water_goal = water_goal_row or 2000

    user_row = await db.get_user(user_id)
    mood_rows = await db.get_mood_history(user_id, limit=1)
    sleep_rows = await db.get_sleep_history(user_id, limit=1)
    headache_count = await db.get_headache_count_today(user_id, today)

    text = format_today_summary(
        today=today,
        water_today=water_today,
        water_goal=water_goal,
        user_row=user_row,
        mood_last=mood_rows[0] if mood_rows else None,
        sleep_last=sleep_rows[0] if sleep_rows else None,
        headache_count=headache_count,
    )
    await message.answer(text)


@router.message(Command("week"))
async def cmd_week(message: Message):
    await _ensure_user(message)
    user_id = message.from_user.id

    dates = week_dates()
    water_week = await db.get_water_week(user_id, dates)
    water_goal_row = await db.get_water_goal(user_id)
    water_goal = water_goal_row or 2000

    mood_rows = await db.get_mood_history(user_id, limit=7)
    sleep_rows = await db.get_sleep_history(user_id, limit=7)
    headache_rows = await db.get_headache_history(user_id, limit=7)

    text = format_week_report(
        water_week=water_week,
        water_goal=water_goal,
        mood_rows=mood_rows,
        sleep_rows=sleep_rows,
        headache_rows=headache_rows,
    )
    await message.answer(text)


@router.message(Command("export"))
async def cmd_export(message: Message):
    await _ensure_user(message)
    user_id = message.from_user.id

    water_rows = await db.get_all_water_logs(user_id)
    mood_rows = await db.get_all_mood_logs(user_id)
    sleep_rows = await db.get_all_sleep_logs(user_id)
    headache_rows = await db.get_all_headache_logs(user_id)

    total = len(water_rows) + len(mood_rows) + len(sleep_rows) + len(headache_rows)
    if total == 0:
        await message.answer("Данных для экспорта нет.")
        return

    csv_bytes = build_csv(water_rows, mood_rows, sleep_rows, headache_rows)
    filename = f"health_export_{date.today().isoformat()}.csv"
    doc = BufferedInputFile(csv_bytes, filename=filename)
    await message.answer_document(
        doc,
        caption=f"📤 Экспорт данных\nЗаписей: {total}",
    )
