from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from keyboards.inline_keyboards import main_menu_keyboard, yes_no_keyboard, cancel_keyboard


def test_main_menu_returns_reply_keyboard():
    kb = main_menu_keyboard()
    assert isinstance(kb, ReplyKeyboardMarkup)
    assert kb.resize_keyboard is True


def test_main_menu_has_six_buttons():
    kb = main_menu_keyboard()
    texts = [btn.text for row in kb.keyboard for btn in row]
    assert "💧 Вода" in texts
    assert "😊 Настроение" in texts
    assert "😴 Сон" in texts
    assert "🤕 Мигрень" in texts
    assert "📊 Статистика" in texts
    assert "⚙️ Профиль" in texts


def test_yes_no_keyboard_returns_inline():
    kb = yes_no_keyboard("confirm")
    assert isinstance(kb, InlineKeyboardMarkup)


def test_yes_no_keyboard_callback_data():
    kb = yes_no_keyboard("confirm")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    callbacks = {btn.callback_data for btn in buttons}
    assert "confirm_yes" in callbacks
    assert "confirm_no" in callbacks


def test_cancel_keyboard_returns_inline():
    kb = cancel_keyboard()
    assert isinstance(kb, InlineKeyboardMarkup)


def test_cancel_keyboard_callback_data():
    kb = cancel_keyboard()
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert buttons[0].callback_data == "cancel"
