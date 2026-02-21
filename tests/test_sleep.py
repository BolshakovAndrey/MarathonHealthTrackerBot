import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.sleep import (
    calc_sleep_avg,
    sleep_recommendation,
    sleep_chart,
    format_sleep_status,
    SLEEP_NORM_MIN,
    SLEEP_NORM_MAX,
)


# --- calc_sleep_avg ---

def test_avg_empty():
    assert calc_sleep_avg([]) == 0.0


def test_avg_single():
    assert calc_sleep_avg([("2026-02-20", 8.0, 3)]) == 8.0


def test_avg_multiple():
    rows = [("2026-02-19", 6.0, 2), ("2026-02-20", 8.0, 3)]
    assert calc_sleep_avg(rows) == 7.0


def test_avg_rounds_to_one_decimal():
    rows = [("d1", 7.0, None), ("d2", 8.0, None), ("d3", 6.0, None)]
    assert calc_sleep_avg(rows) == 7.0


# --- sleep_recommendation ---

def test_rec_no_data():
    text = sleep_recommendation(0.0)
    assert "Начните" in text


def test_rec_underslept():
    text = sleep_recommendation(5.5)
    assert "Недосып" in text
    assert "5.5" in text


def test_rec_overslept():
    text = sleep_recommendation(10.0)
    assert "Пересып" in text


def test_rec_normal():
    text = sleep_recommendation(7.5)
    assert "норм" in text.lower() or "отлично" in text.lower()


def test_rec_exact_min():
    text = sleep_recommendation(SLEEP_NORM_MIN)
    assert "Недосып" not in text


def test_rec_exact_max():
    text = sleep_recommendation(SLEEP_NORM_MAX)
    assert "Пересып" not in text


# --- sleep_chart ---

def test_chart_empty():
    assert "Записей нет" in sleep_chart([])


def test_chart_good_sleep():
    rows = [("2026-02-20", 8.0, 3)]
    chart = sleep_chart(rows)
    assert "🌙" in chart
    assert "02-20" in chart
    assert "8.0ч" in chart


def test_chart_medium_sleep():
    rows = [("2026-02-20", 5.5, 2)]
    chart = sleep_chart(rows)
    assert "🌛" in chart


def test_chart_poor_sleep():
    rows = [("2026-02-20", 3.0, 1)]
    chart = sleep_chart(rows)
    assert "😵" in chart


def test_chart_no_quality():
    rows = [("2026-02-20", 7.0, None)]
    chart = sleep_chart(rows)
    assert "—" in chart


# --- format_sleep_status ---

def test_format_contains_header():
    text = format_sleep_status([])
    assert "Сон" in text


def test_format_contains_recommendation():
    rows = [("2026-02-20", 6.0, 2)]
    text = format_sleep_status(rows)
    assert "💡" in text


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


async def test_log_and_get_sleep(db):
    await db.log_sleep(1, "2026-02-20", 8.0, 3)
    rows = await db.get_sleep_history(1)
    assert len(rows) == 1
    assert rows[0][1] == 8.0
    assert rows[0][2] == 3


async def test_sleep_without_quality(db):
    await db.log_sleep(1, "2026-02-20", 7.5)
    rows = await db.get_sleep_history(1)
    assert rows[0][2] is None


async def test_sleep_history_order(db):
    await db.log_sleep(1, "2026-02-19", 6.0, 2)
    await db.log_sleep(1, "2026-02-20", 8.0, 3)
    rows = await db.get_sleep_history(1)
    # Сортировка по sleep_date DESC — последний день первый
    assert rows[0][0] == "2026-02-20"


async def test_sleep_history_limit(db):
    for day in range(1, 11):
        await db.log_sleep(1, f"2026-02-{day:02d}", float(day % 10 + 5), None)
    rows = await db.get_sleep_history(1, limit=5)
    assert len(rows) == 5


async def test_sleep_history_empty(db):
    rows = await db.get_sleep_history(1)
    assert rows == []


# --- Handler tests ---

def _make_message(text: str, user_id: int = 1) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.answer = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.username = "tester"
    msg.from_user.full_name = "Test User"
    return msg


def _make_callback(data: str, user_id: int = 1) -> MagicMock:
    cb = MagicMock()
    cb.data = data
    cb.answer = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.from_user.username = "tester"
    cb.from_user.full_name = "Test User"
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    return cb


def _make_state(hours: float = 7.0) -> MagicMock:
    st = MagicMock()
    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    st.update_data = AsyncMock()
    st.get_data = AsyncMock(return_value={"sleep_hours": hours})
    return st


async def test_cmd_sleep_shows_status():
    from handlers.sleep import cmd_sleep
    msg = _make_message("/sleep")
    with patch("handlers.sleep.db") as mock_db, patch("handlers.sleep._show_sleep", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        await cmd_sleep(msg)
    mock_db.upsert_user.assert_awaited_once()
    mock_show.assert_awaited_once_with(msg, 1)


async def test_cb_sleep_hours_quick():
    from handlers.sleep import cb_sleep_hours
    cb = _make_callback("sleep_hours:8.0")
    state = _make_state()
    with patch("handlers.sleep.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await cb_sleep_hours(cb, state)
    state.set_state.assert_awaited_once()
    state.update_data.assert_awaited_once_with(sleep_hours=8.0)
    cb.message.edit_text.assert_awaited_once()


async def test_msg_sleep_hours_invalid():
    from handlers.sleep import msg_sleep_hours
    msg = _make_message("abc")
    state = _make_state()
    with patch("handlers.sleep.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_sleep_hours(msg, state)
    msg.answer.assert_awaited_once()
    assert "число" in msg.answer.call_args[0][0]
    state.set_state.assert_not_called()


async def test_msg_sleep_hours_out_of_range():
    from handlers.sleep import msg_sleep_hours
    msg = _make_message("25")
    state = _make_state()
    with patch("handlers.sleep.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_sleep_hours(msg, state)
    assert "24" in msg.answer.call_args[0][0]


async def test_msg_sleep_hours_valid():
    from handlers.sleep import msg_sleep_hours
    msg = _make_message("6.5")
    state = _make_state()
    with patch("handlers.sleep.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_sleep_hours(msg, state)
    state.update_data.assert_awaited_once_with(sleep_hours=6.5)
    state.set_state.assert_awaited_once()
    msg.answer.assert_awaited_once()


async def test_msg_sleep_hours_comma_separator():
    """Запятая в дробном числе должна работать."""
    from handlers.sleep import msg_sleep_hours
    msg = _make_message("7,5")
    state = _make_state()
    with patch("handlers.sleep.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_sleep_hours(msg, state)
    state.update_data.assert_awaited_once_with(sleep_hours=7.5)


async def test_cb_sleep_quality_saves(db):
    from handlers.sleep import cb_sleep_quality
    await db.upsert_user(1, "u", "U")
    cb = _make_callback("sleep_quality:3")
    state = _make_state(8.0)
    with patch("handlers.sleep.db", db), patch("handlers.sleep._show_sleep", new=AsyncMock()):
        await cb_sleep_quality(cb, state)
    state.clear.assert_awaited_once()
    rows = await db.get_sleep_history(1)
    assert rows[0][1] == 8.0
    assert rows[0][2] == 3


async def test_cb_sleep_quality_skip(db):
    from handlers.sleep import cb_sleep_quality
    await db.upsert_user(1, "u", "U")
    cb = _make_callback("sleep_quality:0")
    state = _make_state(7.0)
    with patch("handlers.sleep.db", db), patch("handlers.sleep._show_sleep", new=AsyncMock()):
        await cb_sleep_quality(cb, state)
    rows = await db.get_sleep_history(1)
    assert rows[0][2] is None  # quality = None когда пропущено
