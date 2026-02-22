"""Phase 9: error handling, /help, /cancel."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_message(text: str = "/help", user_id: int = 1) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.answer = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.username = "tester"
    msg.from_user.full_name = "Test User"
    return msg


def _make_state(current_state=None) -> MagicMock:
    st = MagicMock()
    st.get_state = AsyncMock(return_value=current_state)
    st.clear = AsyncMock()
    return st


# --- /help ---

async def test_help_returns_message():
    from handlers.help import cmd_help
    msg = _make_message("/help")
    await cmd_help(msg)
    msg.answer.assert_awaited_once()
    text = msg.answer.call_args[0][0]
    assert "/water" in text
    assert "/mood" in text
    assert "/sleep" in text
    assert "/headache" in text
    assert "/today" in text
    assert "/export" in text


async def test_help_contains_all_commands():
    from handlers.help import cmd_help, _HELP_TEXT
    commands = ["/start", "/profile", "/water", "/mood", "/sleep",
                "/headache", "/today", "/week", "/export", "/cancel", "/help"]
    for cmd in commands:
        assert cmd in _HELP_TEXT, f"{cmd} missing from /help text"


# --- /cancel ---

async def test_cancel_with_active_state():
    from handlers.help import cmd_cancel
    from states.forms import WaterInput
    msg = _make_message("/cancel")
    state = _make_state(current_state=WaterInput.waiting_amount)
    await cmd_cancel(msg, state)
    state.clear.assert_awaited_once()
    msg.answer.assert_awaited_once()
    assert "отменено" in msg.answer.call_args[0][0].lower()


async def test_cancel_without_active_state():
    from handlers.help import cmd_cancel
    msg = _make_message("/cancel")
    state = _make_state(current_state=None)
    await cmd_cancel(msg, state)
    state.clear.assert_awaited_once()
    msg.answer.assert_awaited_once()
    assert "нет активного" in msg.answer.call_args[0][0].lower()


# --- DB error logging ---

async def test_db_execute_logs_on_error(tmp_path, caplog):
    import logging
    from db.database import Database

    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()

    with caplog.at_level(logging.ERROR, logger="db.database"):
        with pytest.raises(Exception):
            await instance.execute("INVALID SQL !!!")

    assert any("DB execute error" in r.message for r in caplog.records)


async def test_db_fetchone_logs_on_error(tmp_path, caplog):
    import logging
    from db.database import Database

    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()

    with caplog.at_level(logging.ERROR, logger="db.database"):
        with pytest.raises(Exception):
            await instance.fetchone("SELECT * FROM nonexistent_table")

    assert any("DB fetchone error" in r.message for r in caplog.records)


async def test_db_fetchall_logs_on_error(tmp_path, caplog):
    import logging
    from db.database import Database

    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()

    with caplog.at_level(logging.ERROR, logger="db.database"):
        with pytest.raises(Exception):
            await instance.fetchall("SELECT * FROM nonexistent_table")

    assert any("DB fetchall error" in r.message for r in caplog.records)


# --- Global error handler ---

async def test_global_error_handler_answers_user():
    """Глобальный обработчик посылает fallback-сообщение и возвращает True."""
    from app import handle_unknown_error
    from aiogram.types import ErrorEvent, Update

    msg = _make_message("/something")
    update = MagicMock(spec=Update)
    update.message = msg
    update.callback_query = None

    event = MagicMock(spec=ErrorEvent)
    event.exception = RuntimeError("boom")
    event.update = update

    result = await handle_unknown_error(event)

    assert result is True
    msg.answer.assert_awaited_once()
    assert "ошибка" in msg.answer.call_args[0][0].lower()


async def test_global_error_handler_handles_callback():
    """Обработчик корректно работает с callback_query обновлением."""
    from app import handle_unknown_error
    from aiogram.types import ErrorEvent, Update

    callback = MagicMock()
    callback.answer = AsyncMock()
    callback.message = _make_message()

    update = MagicMock(spec=Update)
    update.message = None
    update.callback_query = callback

    event = MagicMock(spec=ErrorEvent)
    event.exception = RuntimeError("boom")
    event.update = update

    result = await handle_unknown_error(event)
    assert result is True
