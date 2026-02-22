import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from services.stats import format_today_summary, format_week_report, build_csv
from services.water import week_dates


TODAY = date.today().isoformat()

# --- format_today_summary ---

def _user_row(calories=2000, protein=150, fat=60, carbs=250):
    # (user_id, username, full_name, gender, age, height, weight, activity, goal,
    #  bmr, tdee, calories, protein, fat, carbs, created_at, updated_at)
    return (1, "u", "U", "female", 30, 165, 60, "moderate", "maintain",
            1500.0, 2000.0, calories, protein, fat, carbs, TODAY, TODAY)


def test_today_contains_water_bar():
    text = format_today_summary(TODAY, 1000, 2000, None, None, None, 0)
    assert "Вода" in text
    assert "1000" in text


def test_today_contains_date():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 0)
    assert TODAY in text


def test_today_mood_recorded():
    mood = ("😊", "хорошо", TODAY + " 10:00:00")
    text = format_today_summary(TODAY, 0, 2000, None, mood, None, 0)
    assert "😊" in text
    assert "хорошо" in text


def test_today_mood_not_recorded():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 0)
    assert "не записано" in text


def test_today_sleep_recorded():
    sleep = (TODAY, 8.0, 3)
    text = format_today_summary(TODAY, 0, 2000, None, None, sleep, 0)
    assert "8.0ч" in text


def test_today_sleep_not_recorded():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 0)
    assert "не записан" in text


def test_today_headache_count():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 2)
    assert "2" in text
    assert "эп" in text


def test_today_no_headache():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 0)
    assert "нет" in text.lower()


def test_today_kbju_targets():
    text = format_today_summary(TODAY, 0, 2000, _user_row(), None, None, 0)
    assert "2000 ккал" in text
    assert "150г" in text


def test_today_no_profile():
    text = format_today_summary(TODAY, 0, 2000, None, None, None, 0)
    # Без профиля — нет секции КБЖУ, но не падает
    assert "Сводка" in text


def test_today_mood_from_yesterday():
    """Запись не сегодняшняя — дата должна быть указана."""
    mood = ("😔", None, "2026-02-19 10:00:00")
    text = format_today_summary(TODAY, 0, 2000, None, mood, None, 0)
    assert "2026-02-19" in text


# --- format_week_report ---

def _water_week(val=1500):
    return {d: val for d in week_dates()}


def test_week_contains_water():
    text = format_week_report(_water_week(), 2000, [], [], [])
    assert "Вода" in text


def test_week_water_average():
    text = format_week_report(_water_week(1400), 2000, [], [], [])
    assert "1400" in text


def test_week_mood_trend():
    mood_rows = [("😄", None, "d1"), ("😊", None, "d2"),
                 ("😔", None, "d3"), ("😢", None, "d4")]
    text = format_week_report(_water_week(), 2000, mood_rows, [], [])
    assert "Тренд" in text


def test_week_no_mood():
    text = format_week_report(_water_week(), 2000, [], [], [])
    assert "нет записей" in text


def test_week_sleep_avg():
    sleep_rows = [("2026-02-20", 8.0, 3), ("2026-02-19", 7.0, 2)]
    text = format_week_report(_water_week(), 2000, [], sleep_rows, [])
    assert "7.5ч" in text


def test_week_headache_count():
    headache_rows = [(7, "temples", "stress", 60, "2026-02-20"),
                     (5, None, None, None, "2026-02-19")]
    text = format_week_report(_water_week(), 2000, [], [], headache_rows)
    assert "2" in text
    assert "6.0/10" in text


def test_week_no_headache():
    text = format_week_report(_water_week(), 2000, [], [], [])
    assert "нет" in text.lower()


# --- build_csv ---

def test_csv_contains_water_header():
    data = build_csv([(500, "2026-02-20")], [], [], [])
    text = data.decode("utf-8-sig")
    assert "WATER LOG" in text
    assert "500" in text


def test_csv_contains_mood_header():
    data = build_csv([], [("😊", "ок", "2026-02-20")], [], [])
    text = data.decode("utf-8-sig")
    assert "MOOD LOG" in text
    assert "😊" in text


def test_csv_contains_sleep_header():
    data = build_csv([], [], [("2026-02-20", 8.0, 3)], [])
    text = data.decode("utf-8-sig")
    assert "SLEEP LOG" in text
    assert "8.0" in text


def test_csv_contains_headache_header():
    data = build_csv([], [], [], [(7, "temples", "stress", 60, "2026-02-20")])
    text = data.decode("utf-8-sig")
    assert "HEADACHE LOG" in text
    assert "7" in text


def test_csv_triggers_decoded():
    """Триггеры в экспорте — читаемые метки, не ключи."""
    data = build_csv([], [], [], [(5, None, "stress,food", None, "2026-02-20")])
    text = data.decode("utf-8-sig")
    assert "Стресс" in text
    assert "Еда" in text


def test_csv_empty_data():
    data = build_csv([], [], [], [])
    text = data.decode("utf-8-sig")
    assert "WATER LOG" in text  # заголовки есть даже при пустых данных


def test_csv_returns_bytes():
    assert isinstance(build_csv([], [], [], []), bytes)


# --- DB integration ---

@pytest.fixture
async def db(tmp_path):
    from db.database import Database
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    await instance._run_migrations()
    await instance.upsert_user(1, "u", "U")
    yield instance


async def test_headache_count_today_zero(db):
    count = await db.get_headache_count_today(1, TODAY)
    assert count == 0


async def test_headache_count_today_nonzero(db):
    await db.log_headache(1, intensity=7)
    await db.log_headache(1, intensity=5)
    count = await db.get_headache_count_today(1, TODAY)
    assert count == 2


async def test_get_all_water_logs(db):
    await db.log_water(1, 250)
    await db.log_water(1, 500)
    rows = await db.get_all_water_logs(1)
    assert len(rows) == 2
    assert rows[0][0] == 250


async def test_get_all_mood_logs(db):
    await db.log_mood(1, "😊")
    await db.log_mood(1, "😄", note="хорошо")
    rows = await db.get_all_mood_logs(1)
    assert len(rows) == 2


async def test_get_all_sleep_logs(db):
    await db.log_sleep(1, "2026-02-19", 7.0)
    await db.log_sleep(1, "2026-02-20", 8.0)
    rows = await db.get_all_sleep_logs(1)
    assert len(rows) == 2


async def test_get_all_headache_logs(db):
    await db.log_headache(1, intensity=6)
    rows = await db.get_all_headache_logs(1)
    assert len(rows) == 1
    assert rows[0][0] == 6


# --- Handler smoke tests ---

def _make_message(text: str, user_id: int = 1) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.answer = AsyncMock()
    msg.answer_document = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.username = "tester"
    msg.from_user.full_name = "Test User"
    return msg


async def test_cmd_today_calls_answer(db):
    from handlers.stats import cmd_today
    await db.upsert_user(1, "u", "U")
    msg = _make_message("/today")
    with patch("handlers.stats.db", db):
        await cmd_today(msg)
    msg.answer.assert_awaited_once()


async def test_cmd_week_calls_answer(db):
    from handlers.stats import cmd_week
    await db.upsert_user(1, "u", "U")
    msg = _make_message("/week")
    with patch("handlers.stats.db", db):
        await cmd_week(msg)
    msg.answer.assert_awaited_once()


async def test_cmd_export_no_data(db):
    from handlers.stats import cmd_export
    await db.upsert_user(1, "u", "U")
    msg = _make_message("/export")
    with patch("handlers.stats.db", db):
        await cmd_export(msg)
    assert "нет" in msg.answer.call_args[0][0].lower()


async def test_cmd_export_with_data(db):
    from handlers.stats import cmd_export
    await db.upsert_user(1, "u", "U")
    await db.log_water(1, 500)
    msg = _make_message("/export")
    with patch("handlers.stats.db", db):
        await cmd_export(msg)
    msg.answer_document.assert_awaited_once()
