from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_message(text: str):
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


def _make_state():
    st = MagicMock()
    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_cmd_water_ensures_user_and_shows_status():
    from handlers.water import cmd_water

    msg = _make_message("/water")
    with patch("handlers.water.db") as mock_db, patch("handlers.water._show_water", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        await cmd_water(msg)

    mock_db.upsert_user.assert_awaited_once_with(123, "alice", "Alice Test")
    mock_show.assert_awaited_once_with(msg, 123)


@pytest.mark.asyncio
async def test_cb_water_add_logs_and_refreshes():
    from handlers.water import cb_water_add

    cb = _make_callback("water_add:500")
    with patch("handlers.water.db") as mock_db, patch("handlers.water._show_water", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        mock_db.log_water = AsyncMock()
        await cb_water_add(cb)

    mock_db.log_water.assert_awaited_once_with(123, 500)
    mock_show.assert_awaited_once_with(cb, 123, edit=True)


@pytest.mark.asyncio
async def test_msg_water_amount_rejects_non_numeric():
    from handlers.water import msg_water_amount

    msg = _make_message("abc")
    state = _make_state()
    with patch("handlers.water.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_water_amount(msg, state)

    state.clear.assert_not_called()
    msg.answer.assert_awaited()
    assert "целое число" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_msg_water_amount_accepts_valid_value():
    from handlers.water import msg_water_amount

    msg = _make_message("350")
    state = _make_state()
    with patch("handlers.water.db") as mock_db, patch("handlers.water._show_water", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        mock_db.log_water = AsyncMock()
        await msg_water_amount(msg, state)

    state.clear.assert_awaited_once()
    mock_db.log_water.assert_awaited_once_with(123, 350)
    mock_show.assert_awaited_once_with(msg, 123)


@pytest.mark.asyncio
async def test_msg_water_goal_rejects_out_of_range():
    from handlers.water import msg_water_goal

    msg = _make_message("900")
    state = _make_state()
    with patch("handlers.water.db") as mock_db:
        mock_db.upsert_user = AsyncMock()
        await msg_water_goal(msg, state)

    state.clear.assert_not_called()
    msg.answer.assert_awaited()
    assert "от 1000 до 5000" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_msg_water_goal_sets_goal_and_shows_status():
    from handlers.water import msg_water_goal

    msg = _make_message("2400")
    state = _make_state()
    with patch("handlers.water.db") as mock_db, patch("handlers.water._show_water", new=AsyncMock()) as mock_show:
        mock_db.upsert_user = AsyncMock()
        mock_db.set_water_goal = AsyncMock()
        await msg_water_goal(msg, state)

    state.clear.assert_awaited_once()
    mock_db.set_water_goal.assert_awaited_once_with(123, 2400)
    mock_show.assert_awaited_once_with(msg, 123)
