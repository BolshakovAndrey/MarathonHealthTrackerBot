from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import main_menu_keyboard

router = Router()


def _setup_profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🧮 Начать настройку профиля", callback_data="profile_setup_start")
    return builder.as_markup()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    if user is None:
        return

    username = user.username or ""
    full_name = (user.full_name or "").strip() or str(user.id)
    await db.upsert_user(user_id=user.id, username=username, full_name=full_name)

    has_profile = await db.has_profile(user.id)
    if has_profile:
        text = (
            f"Привет, <b>{full_name}</b>!\n\n"
            "Бот готов к ежедневному трекингу:\n"
            "• вода\n• настроение\n• сон\n• мигрень\n\n"
            "Открыть профиль: /profile"
        )
        await message.answer(text, reply_markup=main_menu_keyboard())
        return

    text = (
        f"Привет, <b>{full_name}</b>!\n\n"
        "Я помогу вести трекер здоровья и считать КБЖУ.\n"
        "Сначала нужно заполнить профиль."
    )
    await message.answer(text, reply_markup=_setup_profile_keyboard())
