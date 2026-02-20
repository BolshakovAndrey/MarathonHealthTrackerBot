import pytest
from datetime import date, timedelta
from unittest.mock import patch

from services.water import (
    calc_default_goal,
    progress_bar,
    week_dates,
    week_chart,
    format_water_status,
    BLOCKS,
    FILLED,
    EMPTY,
)


# --- calc_default_goal ---

def test_goal_from_weight():
    assert calc_default_goal("female", 60.0) == 1800


def test_goal_from_weight_male():
    assert calc_default_goal("male", 80.0) == 2400


def test_goal_female_default_no_weight():
    assert calc_default_goal("female", None) == 2000


def test_goal_male_default_no_weight():
    assert calc_default_goal("male", None) == 2500


def test_goal_none_gender_no_weight():
    assert calc_default_goal(None, None) == 2500


def test_goal_clamped_min():
    assert calc_default_goal("female", 30.0) == 1500  # 30*30=900 → clamp 1500


def test_goal_clamped_max():
    assert calc_default_goal("male", 200.0) == 4000  # 200*30=6000 → clamp 4000


# --- progress_bar ---

def test_progress_bar_empty():
    bar = progress_bar(0, 2000)
    assert EMPTY * BLOCKS in bar
    assert "0/2000" in bar
    assert "0%" in bar


def test_progress_bar_full():
    bar = progress_bar(2000, 2000)
    assert FILLED * BLOCKS in bar
    assert "100%" in bar


def test_progress_bar_half():
    bar = progress_bar(1000, 2000)
    assert "50%" in bar
    filled_count = bar.count(FILLED)
    assert filled_count == BLOCKS // 2


def test_progress_bar_over_goal():
    bar = progress_bar(3000, 2000)
    assert "100%" in bar
    assert FILLED * BLOCKS in bar


def test_progress_bar_zero_goal():
    bar = progress_bar(500, 0)
    assert "500 мл" in bar


# --- week_dates ---

def test_week_dates_length():
    assert len(week_dates()) == 7


def test_week_dates_order():
    dates = week_dates(date(2026, 2, 20))
    assert dates[0] == "2026-02-14"
    assert dates[-1] == "2026-02-20"


def test_week_dates_consecutive():
    dates = week_dates()
    for i in range(1, len(dates)):
        d1 = date.fromisoformat(dates[i - 1])
        d2 = date.fromisoformat(dates[i])
        assert (d2 - d1).days == 1


# --- week_chart ---

def test_week_chart_full_day():
    totals = {"2026-02-20": 2000}
    chart = week_chart(totals, 2000)
    assert "💧" in chart


def test_week_chart_half_day():
    totals = {"2026-02-20": 1000}
    chart = week_chart(totals, 2000)
    assert "🔹" in chart


def test_week_chart_empty_day():
    totals = {"2026-02-20": 0}
    chart = week_chart(totals, 2000)
    assert "▫️" in chart


def test_week_chart_shows_date():
    totals = {"2026-02-20": 500}
    chart = week_chart(totals, 2000)
    assert "02-20" in chart


# --- format_water_status ---

def test_format_water_status_contains_sections():
    week = {d: 1500 for d in week_dates(date(2026, 2, 20))}
    text = format_water_status(1200, 2000, week)
    assert "Вода сегодня" in text
    assert "За 7 дней" in text
    assert "Среднее за неделю" in text
    assert "1500 мл" in text


def test_format_water_status_average():
    week = {d: 1000 for d in week_dates(date(2026, 2, 20))}
    text = format_water_status(0, 2000, week)
    assert "1000 мл" in text


# --- DB water methods (integration with SQLite) ---

@pytest.fixture
async def db(tmp_path):
    from db.database import Database
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    await instance._run_migrations()
    await instance.upsert_user(1, "u", "U")
    yield instance


async def test_log_and_get_water_today(db):
    today = date.today().isoformat()
    await db.log_water(1, 250)
    await db.log_water(1, 500)
    total = await db.get_water_today(1, today)
    assert total == 750


async def test_get_water_week_empty(db):
    dates = week_dates()
    week = await db.get_water_week(1, dates)
    assert all(v == 0 for v in week.values())
    assert len(week) == 7


async def test_get_water_week_with_data(db):
    today = date.today().isoformat()
    await db.log_water(1, 300)
    await db.log_water(1, 700)
    dates = week_dates()
    week = await db.get_water_week(1, dates)
    assert week[today] == 1000


async def test_set_and_get_water_goal(db):
    await db.set_water_goal(1, 2500)
    goal = await db.get_water_goal(1)
    assert goal == 2500


async def test_get_water_goal_none_by_default(db):
    goal = await db.get_water_goal(1)
    assert goal is None
