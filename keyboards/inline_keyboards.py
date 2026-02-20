from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💧 Вода"), KeyboardButton(text="😊 Настроение")],
            [KeyboardButton(text="😴 Сон"), KeyboardButton(text="🤕 Мигрень")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Профиль")],
        ],
        resize_keyboard=True,
    )


def yes_no_keyboard(prefix: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да", callback_data=f"{prefix}_yes"),
        InlineKeyboardButton(text="Нет", callback_data=f"{prefix}_no"),
    )
    return builder.as_markup()


def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return builder.as_markup()


# Backward-compatible aliases from project plan naming.
def main_menu() -> ReplyKeyboardMarkup:
    return main_menu_keyboard()


def yes_no(prefix: str):
    return yes_no_keyboard(prefix)


def cancel():
    return cancel_keyboard()
