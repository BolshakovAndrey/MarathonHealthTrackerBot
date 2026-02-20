from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_message(text: str = "/start"):
    msg = MagicMock()
    msg.text = text
    msg.answer = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123
    msg.from_user.username = "alice"
    msg.from_user.full_name = "Alice Test"
    return msg


def _make_callback(data: str):
    cb = MagicMock()
    cb.data = data
    cb.answer = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = 123
    cb.from_user.username = "alice"
    cb.from_user.full_name = "Alice Test"
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    return cb


def _make_state(data: dict | None = None):
    st = MagicMock()
    st.set_state = AsyncMock()
    st.update_data = AsyncMock()
    st.get_data = AsyncMock(return_value=data or {})
    st.clear = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_start_shows_profile_setup_for_new_user():
    from handlers.start import cmd_start
    msg = _make_message("/start")
    with patch("handlers.start.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        mock_db.has_profile = AsyncMock(return_value=False)
        await cmd_start(msg)
    msg.answer.assert_called_once()
    text = msg.answer.call_args[0][0]
    assert "заполнить профиль" in text.lower()


@pytest.mark.asyncio
async def test_start_shows_main_menu_for_existing_profile():
    from handlers.start import cmd_start
    msg = _make_message("/start")
    with patch("handlers.start.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        mock_db.has_profile = AsyncMock(return_value=True)
        await cmd_start(msg)
    text = msg.answer.call_args[0][0]
    assert "ежедневному трекингу" in text.lower()


@pytest.mark.asyncio
async def test_profile_command_prompts_setup_when_empty():
    from handlers.profile import cmd_profile
    msg = _make_message("/profile")
    with patch("handlers.profile.db") as mock_db:
        mock_db.get_user = AsyncMock(return_value=None)
        await cmd_profile(msg)
    text = msg.answer.call_args[0][0]
    assert "не заполнен" in text.lower()


@pytest.mark.asyncio
async def test_profile_command_renders_saved_profile():
    from handlers.profile import cmd_profile
    msg = _make_message("/profile")
    row = (
        123, "alice", "Alice Test", "female", 30, 168.0, 62.0,
        "moderate", "maintain", 1350.0, 2092.5, 2092, 157, 58, 235,
        "2026-01-01", "2026-01-01",
    )
    with patch("handlers.profile.db") as mock_db:
        mock_db.get_user = AsyncMock(return_value=row)
        await cmd_profile(msg)
    text = msg.answer.call_args[0][0]
    assert "ваш профиль" in text.lower()
    assert "кбжу" in text.lower()


@pytest.mark.asyncio
async def test_age_validation_rejects_invalid_input():
    from handlers.profile import msg_age
    msg = _make_message("abc")
    state = _make_state()
    await msg_age(msg, state)
    text = msg.answer.call_args[0][0]
    assert "числом" in text.lower()


@pytest.mark.asyncio
async def test_goal_callback_saves_profile_and_clears_state():
    from services.kbju import KBJUResult
    from handlers.profile import cb_goal

    cb = _make_callback("goal:maintain")
    state = _make_state(
        data={
            "gender": "female",
            "age": 30,
            "height": 168.0,
            "weight": 62.0,
            "activity_level": "moderate",
        }
    )

    with patch("handlers.profile.db") as mock_db, \
         patch("handlers.profile.calculate_kbju") as mock_calc:
        mock_db.upsert_user = AsyncMock()
        mock_db.update_profile = AsyncMock()
        mock_calc.return_value = KBJUResult(
            bmr=1350.0, tdee=2092.5, calories=2092, protein=157, fat=58, carbs=235
        )
        await cb_goal(cb, state)

    state.clear.assert_called_once()
    mock_db.update_profile.assert_called_once()
    cb.message.edit_text.assert_called_once()
