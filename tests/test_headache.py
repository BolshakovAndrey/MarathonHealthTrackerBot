import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.headache import (
    LOCATIONS, TRIGGERS, DURATIONS,
    triggers_to_str, triggers_from_str,
    format_duration, format_headache_entry,
    headache_analytics, format_headache_status,
    LOCATION_LABELS, TRIGGER_LABELS,
)


# --- triggers_to_str / triggers_from_str ---

def test_triggers_to_str_empty():
    assert triggers_to_str([]) is None


def test_triggers_to_str_single():
    assert triggers_to_str(["stress"]) == "stress"


def test_triggers_to_str_multiple():
    assert triggers_to_str(["stress", "sleep"]) == "stress,sleep"


def test_triggers_from_str_none():
    assert triggers_from_str(None) == []


def test_triggers_from_str_empty():
    assert triggers_from_str("") == []


def test_triggers_from_str_single():
    assert triggers_from_str("stress") == ["stress"]


def test_triggers_from_str_multiple():
    assert triggers_from_str("stress,sleep,food") == ["stress", "sleep", "food"]


def test_triggers_roundtrip():
    original = ["stress", "weather"]
    assert triggers_from_str(triggers_to_str(original)) == original


# --- format_duration ---

def test_format_duration_none():
    assert format_duration(None) == "—"


def test_format_duration_minutes():
    assert format_duration(30) == "30 мин"


def test_format_duration_exact_hour():
    assert format_duration(60) == "1ч"


def test_format_duration_fractional():
    assert format_duration(90) == "1.5ч"


def test_format_duration_large():
    assert format_duration(480) == "8ч"


# --- format_headache_entry ---

def _row(intensity=5, location="temples", triggers="stress,sleep", duration=60,
         logged_at="2026-02-20 14:00:00"):
    return (intensity, location, triggers, duration, logged_at)


def test_entry_contains_intensity():
    text = format_headache_entry(_row(intensity=7))
    assert "7/10" in text


def test_entry_contains_location():
    text = format_headache_entry(_row(location="temples"))
    assert LOCATION_LABELS["temples"] in text


def test_entry_contains_triggers():
    text = format_headache_entry(_row(triggers="stress,food"))
    assert TRIGGER_LABELS["stress"] in text
    assert TRIGGER_LABELS["food"] in text


def test_entry_contains_duration():
    text = format_headache_entry(_row(duration=60))
    assert "1ч" in text


def test_entry_date():
    text = format_headache_entry(_row(logged_at="2026-02-20 10:00"))
    assert "2026-02-20" in text


def test_entry_high_intensity_icon():
    text = format_headache_entry(_row(intensity=9))
    assert "🔴" in text


def test_entry_mid_intensity_icon():
    text = format_headache_entry(_row(intensity=6))
    assert "🟠" in text


def test_entry_low_intensity_icon():
    text = format_headache_entry(_row(intensity=3))
    assert "🟡" in text


# --- headache_analytics ---

def test_analytics_empty():
    text = headache_analytics([])
    assert "нет" in text.lower()


def test_analytics_avg_intensity():
    rows = [_row(intensity=6), _row(intensity=8)]
    text = headache_analytics(rows)
    assert "7.0/10" in text


def test_analytics_total_count():
    rows = [_row(), _row(), _row()]
    text = headache_analytics(rows)
    assert "3" in text


def test_analytics_top_trigger():
    rows = [_row(triggers="stress"), _row(triggers="stress"), _row(triggers="sleep")]
    text = headache_analytics(rows)
    assert TRIGGER_LABELS["stress"] in text


def test_analytics_top_location():
    rows = [_row(location="temples"), _row(location="temples"), _row(location="forehead")]
    text = headache_analytics(rows)
    assert LOCATION_LABELS["temples"] in text


# --- format_headache_status ---

def test_status_empty():
    text = format_headache_status([])
    assert "нет" in text.lower() or "Записей" in text


def test_status_has_entries():
    rows = [_row(intensity=5)]
    text = format_headache_status(rows)
    assert "5/10" in text
    assert "Аналитика" in text


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


async def test_log_and_get_headache(db):
    await db.log_headache(1, intensity=7, location="temples",
                          triggers="stress,sleep", duration=60)
    rows = await db.get_headache_history(1)
    assert len(rows) == 1
    assert rows[0][0] == 7
    assert rows[0][1] == "temples"
    assert rows[0][2] == "stress,sleep"
    assert rows[0][3] == 60


async def test_log_headache_minimal(db):
    await db.log_headache(1, intensity=3)
    rows = await db.get_headache_history(1)
    assert rows[0][0] == 3
    assert rows[0][1] is None
    assert rows[0][2] is None
    assert rows[0][3] is None


async def test_headache_history_limit(db):
    for i in range(15):
        await db.log_headache(1, intensity=i % 10 + 1)
    rows = await db.get_headache_history(1, limit=5)
    assert len(rows) == 5


async def test_headache_history_order_desc(db):
    await db.log_headache(1, intensity=3)
    await db.log_headache(1, intensity=9)
    rows = await db.get_headache_history(1)
    assert rows[0][0] == 9  # последняя запись — первая


async def test_headache_history_empty(db):
    rows = await db.get_headache_history(1)
    assert rows == []


# --- Handler tests ---

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
    cb.message.edit_reply_markup = AsyncMock()
    cb.message.answer = AsyncMock()
    return cb


def _make_message(text: str, user_id: int = 1) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.answer = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.username = "tester"
    msg.from_user.full_name = "Test User"
    return msg


def _make_state(**data) -> MagicMock:
    """State mock, который реально обновляет данные при update_data."""
    st = MagicMock()
    _store = dict(data)

    async def _update(**kwargs):
        _store.update(kwargs)

    async def _get():
        return dict(_store)

    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    st.update_data = AsyncMock(side_effect=_update)
    st.get_data = AsyncMock(side_effect=_get)
    return st


async def test_cb_hd_start_sets_state():
    from handlers.headache import cb_hd_start
    cb = _make_callback("hd_start")
    state = _make_state()
    with patch("handlers.headache.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await cb_hd_start(cb, state)
    state.set_state.assert_awaited_once()
    cb.message.edit_text.assert_awaited_once()


async def test_cb_hd_intensity_advances_state():
    from handlers.headache import cb_hd_intensity
    cb = _make_callback("hd_intensity:7")
    state = _make_state()
    await cb_hd_intensity(cb, state)
    state.update_data.assert_awaited_once_with(intensity=7)
    state.set_state.assert_awaited_once()
    cb.message.edit_text.assert_awaited_once()


async def test_cb_hd_location_sets_location():
    from handlers.headache import cb_hd_location
    cb = _make_callback("hd_location:temples")
    state = _make_state(triggers=[])
    await cb_hd_location(cb, state)
    update_call = state.update_data.call_args
    assert update_call.kwargs["location"] == "temples"
    state.set_state.assert_awaited_once()


async def test_cb_hd_location_skip():
    from handlers.headache import cb_hd_location
    cb = _make_callback("hd_location:skip")
    state = _make_state(triggers=[])
    await cb_hd_location(cb, state)
    update_call = state.update_data.call_args
    assert update_call.kwargs["location"] is None


async def test_cb_hd_trigger_toggle_add():
    from handlers.headache import cb_hd_trigger_toggle
    cb = _make_callback("hd_trigger:stress")
    state = _make_state(triggers=[])
    await cb_hd_trigger_toggle(cb, state)
    state.update_data.assert_awaited_once_with(triggers=["stress"])
    cb.message.edit_reply_markup.assert_awaited_once()


async def test_cb_hd_trigger_toggle_remove():
    from handlers.headache import cb_hd_trigger_toggle
    cb = _make_callback("hd_trigger:stress")
    state = _make_state(triggers=["stress", "sleep"])
    await cb_hd_trigger_toggle(cb, state)
    updated = state.update_data.call_args.kwargs["triggers"]
    assert "stress" not in updated
    assert "sleep" in updated


async def test_cb_hd_triggers_confirm_advances():
    from handlers.headache import cb_hd_triggers_confirm
    cb = _make_callback("hd_triggers_done")
    state = _make_state(triggers=["stress"])
    await cb_hd_triggers_confirm(cb, state)
    state.set_state.assert_awaited_once()
    cb.message.edit_text.assert_awaited_once()


async def test_cb_hd_duration_saves(db):
    from handlers.headache import cb_hd_duration
    await db.upsert_user(1, "u", "U")
    cb = _make_callback("hd_duration:60")
    state = _make_state(intensity=7, location="temples",
                        triggers=["stress"], duration=None)
    with patch("handlers.headache.db", db), \
         patch("handlers.headache._show_headache", new=AsyncMock()):
        await cb_hd_duration(cb, state)
    state.clear.assert_awaited_once()
    rows = await db.get_headache_history(1)
    assert rows[0][0] == 7
    assert rows[0][3] == 60


async def test_msg_hd_duration_invalid():
    from handlers.headache import msg_hd_duration_custom
    msg = _make_message("много")
    state = _make_state(intensity=5, location=None, triggers=[])
    with patch("handlers.headache.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_hd_duration_custom(msg, state)
    msg.answer.assert_awaited_once()
    assert "минут" in msg.answer.call_args[0][0]
    state.clear.assert_not_called()


async def test_msg_hd_duration_out_of_range():
    from handlers.headache import msg_hd_duration_custom
    msg = _make_message("9999")
    state = _make_state(intensity=5, location=None, triggers=[])
    with patch("handlers.headache.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_hd_duration_custom(msg, state)
    assert "1440" in msg.answer.call_args[0][0]


async def test_msg_hd_duration_valid(db):
    from handlers.headache import msg_hd_duration_custom
    await db.upsert_user(1, "u", "U")
    msg = _make_message("45")
    state = _make_state(intensity=6, location="forehead", triggers=["food"])
    with patch("handlers.headache.db", db):
        await msg_hd_duration_custom(msg, state)
    state.clear.assert_awaited_once()
    rows = await db.get_headache_history(1)
    assert rows[0][3] == 45
