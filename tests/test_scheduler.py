import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.scheduler import (
    water_reminder_text,
    evening_checkin_text,
    job_water_reminder,
    job_evening_checkin,
    setup_scheduler,
)


# --- water_reminder_text ---

def test_water_reminder_zero_drunk():
    text = water_reminder_text(0, 2000)
    assert "ещё не пили" in text
    assert "2000" in text


def test_water_reminder_partial():
    text = water_reminder_text(500, 2000)
    assert "500" in text
    assert "1500" in text  # remaining
    assert "25%" in text


def test_water_reminder_full():
    text = water_reminder_text(2000, 2000)
    assert "100%" in text
    assert "0" in text  # remaining = 0


def test_water_reminder_goal_zero():
    # не падает при нулевой цели
    text = water_reminder_text(0, 0)
    assert isinstance(text, str)


# --- evening_checkin_text ---

def test_evening_all_done():
    text = evening_checkin_text(has_mood=True, has_sleep=True, water_pct=90)
    assert "Отличный" in text


def test_evening_missing_mood():
    text = evening_checkin_text(has_mood=False, has_sleep=True, water_pct=90)
    assert "настроение" in text


def test_evening_missing_sleep():
    text = evening_checkin_text(has_mood=True, has_sleep=False, water_pct=90)
    assert "сон" in text


def test_evening_low_water():
    text = evening_checkin_text(has_mood=True, has_sleep=True, water_pct=50)
    assert "вода" in text.lower()
    assert "50%" in text


def test_evening_all_missing():
    text = evening_checkin_text(has_mood=False, has_sleep=False, water_pct=0)
    assert "настроение" in text
    assert "сон" in text
    assert "вода" in text.lower()


def test_evening_water_at_boundary():
    # 80% — граничное, не должны упоминать воду
    text = evening_checkin_text(has_mood=True, has_sleep=True, water_pct=80)
    assert "Отличный" in text


# --- setup_scheduler ---

def test_setup_scheduler_returns_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    bot = MagicMock()
    scheduler = setup_scheduler(bot)
    assert isinstance(scheduler, AsyncIOScheduler)


def test_setup_scheduler_has_two_jobs():
    bot = MagicMock()
    scheduler = setup_scheduler(bot)
    jobs = scheduler.get_jobs()
    assert len(jobs) == 2


def test_setup_scheduler_job_ids():
    bot = MagicMock()
    scheduler = setup_scheduler(bot)
    ids = {j.id for j in scheduler.get_jobs()}
    assert "water_reminder" in ids
    assert "evening_checkin" in ids


# --- DB integration ---

@pytest.fixture
async def db(tmp_path):
    from db.database import Database
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    await instance._run_migrations()
    yield instance


async def test_get_all_users_empty(db):
    users = await db.get_all_users()
    assert users == []


async def test_get_all_users_returns_all(db):
    await db.upsert_user(1, "alice", "Alice")
    await db.upsert_user(2, "bob", "Bob")
    users = await db.get_all_users()
    assert len(users) == 2
    user_ids = {u[0] for u in users}
    assert {1, 2} == user_ids


# --- job_water_reminder ---

async def test_job_water_reminder_sends_to_users(db):
    await db.upsert_user(1, "u", "U")
    await db.upsert_user(2, "u2", "U2")

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("services.scheduler.db", db), \
         patch("services.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 10  # до 14:00 — всех оповещаем
        await job_water_reminder(bot)

    assert bot.send_message.await_count == 2


async def test_job_water_reminder_skips_above_50pct_after_14(db):
    from datetime import date
    today = date.today().isoformat()
    await db.upsert_user(1, "u", "U")
    await db.set_water_goal(1, 2000)
    await db.log_water(1, 1100)  # > 50% цели

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("services.scheduler.db", db), \
         patch("services.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 16  # после 14:00
        await job_water_reminder(bot)

    bot.send_message.assert_not_called()


async def test_job_water_reminder_sends_below_50pct_after_14(db):
    await db.upsert_user(1, "u", "U")
    await db.set_water_goal(1, 2000)
    await db.log_water(1, 400)  # < 50% цели

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("services.scheduler.db", db), \
         patch("services.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 16
        await job_water_reminder(bot)

    bot.send_message.assert_awaited_once()


async def test_job_water_reminder_ignores_blocked_users(db):
    await db.upsert_user(1, "u", "U")

    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=Exception("Forbidden: bot was blocked"))

    with patch("services.scheduler.db", db), \
         patch("services.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 10
        await job_water_reminder(bot)  # не должен падать


# --- job_evening_checkin ---

async def test_job_evening_checkin_sends_to_users(db):
    await db.upsert_user(1, "u", "U")

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("services.scheduler.db", db):
        await job_evening_checkin(bot)

    bot.send_message.assert_awaited_once()
    call_args = bot.send_message.call_args
    assert call_args[0][0] == 1  # user_id


async def test_job_evening_checkin_ignores_blocked(db):
    await db.upsert_user(1, "u", "U")

    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=Exception("Forbidden"))

    with patch("services.scheduler.db", db):
        await job_evening_checkin(bot)  # не должен падать
