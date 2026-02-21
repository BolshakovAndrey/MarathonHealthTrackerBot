import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.mood import (
    MOOD_EMOJIS,
    MOOD_SCORES,
    calc_trend,
    mood_stats,
    format_mood_history,
)


# --- calc_trend ---

def test_trend_stable_single_entry():
    assert calc_trend([("😊", None, "2026-02-20")]) == "стабильно"


def test_trend_stable_empty():
    assert calc_trend([]) == "стабильно"


def test_trend_improving():
    # Новые (первые) = хорошее настроение, старые (последние) = плохое
    rows = [("😄", None, "2026-02-20"), ("😊", None, "2026-02-19"),
            ("😔", None, "2026-02-18"), ("😢", None, "2026-02-17")]
    assert calc_trend(rows) == "улучшается"


def test_trend_worsening():
    rows = [("😢", None, "2026-02-20"), ("😔", None, "2026-02-19"),
            ("😊", None, "2026-02-18"), ("😄", None, "2026-02-17")]
    assert calc_trend(rows) == "ухудшается"


def test_trend_stable_equal_scores():
    rows = [("😐", None, "2026-02-20"), ("😐", None, "2026-02-19"),
            ("😐", None, "2026-02-18"), ("😐", None, "2026-02-17")]
    assert calc_trend(rows) == "стабильно"


def test_trend_two_entries_same():
    rows = [("🙂", None, "2026-02-20"), ("🙂", None, "2026-02-19")]
    assert calc_trend(rows) == "стабильно"


# --- mood_stats ---

def test_mood_stats_empty():
    assert mood_stats([]) == {}


def test_mood_stats_single():
    rows = [("😊", None, "2026-02-20")]
    assert mood_stats(rows) == {"😊": 1}


def test_mood_stats_multiple():
    rows = [("😊", None, "d1"), ("😊", None, "d2"), ("😄", None, "d3")]
    stats = mood_stats(rows)
    assert stats["😊"] == 2
    assert stats["😄"] == 1


# --- format_mood_history ---

def test_format_empty():
    text = format_mood_history([])
    assert "Записей ещё нет" in text


def test_format_contains_emoji():
    rows = [("😊", None, "2026-02-20 10:00:00")]
    text = format_mood_history(rows)
    assert "😊" in text
    assert "2026-02-20" in text


def test_format_contains_note():
    rows = [("😄", "Хороший день", "2026-02-20")]
    text = format_mood_history(rows)
    assert "Хороший день" in text


def test_format_contains_trend():
    rows = [("😊", None, "2026-02-20")]
    text = format_mood_history(rows)
    assert "Тренд" in text


def test_format_contains_stats():
    rows = [("😊", None, "2026-02-20"), ("😊", None, "2026-02-19")]
    text = format_mood_history(rows)
    assert "😊×2" in text


def test_all_emojis_have_scores():
    for emoji in MOOD_EMOJIS:
        assert emoji in MOOD_SCORES


# --- DB integration tests ---

@pytest.fixture
async def db(tmp_path):
    from db.database import Database
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    await instance._run_migrations()
    await instance.upsert_user(1, "u", "U")
    yield instance


async def test_log_and_get_mood(db):
    await db.log_mood(1, "😊")
    rows = await db.get_mood_history(1)
    assert len(rows) == 1
    assert rows[0][0] == "😊"
    assert rows[0][1] is None


async def test_log_mood_with_note(db):
    await db.log_mood(1, "😄", note="Отличный день")
    rows = await db.get_mood_history(1)
    assert rows[0][1] == "Отличный день"


async def test_mood_history_limit(db):
    for _ in range(10):
        await db.log_mood(1, "😐")
    rows = await db.get_mood_history(1, limit=5)
    assert len(rows) == 5


async def test_mood_history_order_desc(db):
    await db.log_mood(1, "😔")
    await db.log_mood(1, "😄")
    rows = await db.get_mood_history(1)
    assert rows[0][0] == "😄"  # последняя запись — первая в результате


async def test_mood_history_empty(db):
    rows = await db.get_mood_history(1)
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


def _make_state(emoji: str = "😊") -> MagicMock:
    st = MagicMock()
    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    st.update_data = AsyncMock()
    st.get_data = AsyncMock(return_value={"mood_emoji": emoji})
    return st


async def test_cmd_mood_shows_history():
    from handlers.mood import cmd_mood
    msg = _make_message("/mood")
    with patch("handlers.mood.db") as mock_db, patch("handlers.mood._show_mood", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        await cmd_mood(msg)
    mock_db.upsert_user.assert_awaited_once_with(1, "tester", "Test User")
    mock_show.assert_awaited_once_with(msg, 1)


async def test_cb_mood_pick_valid_emoji():
    from handlers.mood import cb_mood_pick
    cb = _make_callback("mood_pick:😊")
    state = _make_state()
    with patch("handlers.mood.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await cb_mood_pick(cb, state)
    state.set_state.assert_awaited_once()
    state.update_data.assert_awaited_once_with(mood_emoji="😊")
    cb.message.edit_text.assert_awaited_once()


async def test_cb_mood_pick_invalid_emoji():
    from handlers.mood import cb_mood_pick
    cb = _make_callback("mood_pick:🍕")
    state = _make_state()
    with patch("handlers.mood.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await cb_mood_pick(cb, state)
    cb.answer.assert_awaited_once()
    state.set_state.assert_not_called()


async def test_cb_mood_skip_note_saves_without_note(db):
    from handlers.mood import cb_mood_skip_note
    await db.upsert_user(1, "u", "U")
    cb = _make_callback("skip")
    state = _make_state("😄")
    with patch("handlers.mood.db", db), patch("handlers.mood._show_mood", new=AsyncMock()):
        await cb_mood_skip_note(cb, state)
    state.clear.assert_awaited_once()
    rows = await db.get_mood_history(1)
    assert rows[0][0] == "😄"
    assert rows[0][1] is None


async def test_msg_mood_note_too_long():
    from handlers.mood import msg_mood_note
    msg = _make_message("x" * 501)
    state = _make_state()
    with patch("handlers.mood.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_mood_note(msg, state)
    msg.answer.assert_awaited_once()
    assert "500" in msg.answer.call_args[0][0]
    state.clear.assert_not_called()


async def test_msg_mood_note_valid(db):
    from handlers.mood import msg_mood_note
    await db.upsert_user(1, "u", "U")
    msg = _make_message("Хороший день")
    state = _make_state("😊")
    with patch("handlers.mood.db", db), patch("handlers.mood._show_mood", new=AsyncMock()):
        await msg_mood_note(msg, state)
    state.clear.assert_awaited_once()
    rows = await db.get_mood_history(1)
    assert rows[0][0] == "😊"
    assert rows[0][1] == "Хороший день"
