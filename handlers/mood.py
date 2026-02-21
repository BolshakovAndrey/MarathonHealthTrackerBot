from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import skip_cancel_keyboard
from services.mood import MOOD_EMOJIS, format_mood_history
from states.forms import MoodInput

router = Router()

_HISTORY_LIMIT = 7


def _mood_keyboard():
    builder = InlineKeyboardBuilder()
    for emoji in MOOD_EMOJIS:
        builder.button(text=emoji, callback_data=f"mood_pick:{emoji}")
    builder.adjust(4)  # 2 ряда по 4
    builder.row()
    builder.button(text="📋 История", callback_data="mood_history")
    return builder.as_markup()


async def _ensure_user(src: Message | CallbackQuery):
    user = src.from_user
    await db.upsert_user(user.id, user.username or "", user.full_name or "")


async def _show_mood(target: Message | CallbackQuery, user_id: int, edit: bool = False):
    rows = await db.get_mood_history(user_id, _HISTORY_LIMIT)
    text = format_mood_history(rows)
    kb = _mood_keyboard()

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(text, reply_markup=kb)
        if isinstance(target, CallbackQuery):
            await target.answer()


@router.message(Command("mood"))
@router.message(F.text == "😊 Настроение")
async def cmd_mood(message: Message):
    await _ensure_user(message)
    await _show_mood(message, message.from_user.id)


@router.callback_query(F.data.startswith("mood_pick:"))
async def cb_mood_pick(callback: CallbackQuery, state: FSMContext):
    await _ensure_user(callback)
    emoji = callback.data.split(":", 1)[1]
    if emoji not in MOOD_EMOJIS:
        await callback.answer("Неизвестный emoji", show_alert=True)
        return
    await state.set_state(MoodInput.waiting_note)
    await state.update_data(mood_emoji=emoji)
    await callback.message.edit_text(
        f"Записал {emoji}\n\nДобавьте заметку или пропустите:",
        reply_markup=skip_cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "skip", MoodInput.waiting_note)
async def cb_mood_skip_note(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    emoji = data.get("mood_emoji", "")
    await state.clear()
    await db.log_mood(callback.from_user.id, emoji, note=None)
    await _show_mood(callback, callback.from_user.id, edit=True)


@router.message(MoodInput.waiting_note)
async def msg_mood_note(message: Message, state: FSMContext):
    await _ensure_user(message)
    data = await state.get_data()
    emoji = data.get("mood_emoji", "")
    note = (message.text or "").strip()
    if len(note) > 500:
        await message.answer("Заметка слишком длинная (максимум 500 символов).")
        return
    await state.clear()
    await db.log_mood(message.from_user.id, emoji, note=note or None)
    await _show_mood(message, message.from_user.id)


@router.callback_query(F.data == "mood_history")
async def cb_mood_history(callback: CallbackQuery):
    await _ensure_user(callback)
    await _show_mood(callback, callback.from_user.id, edit=True)
