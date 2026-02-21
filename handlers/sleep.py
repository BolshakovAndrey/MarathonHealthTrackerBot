from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import cancel_keyboard
from services.sleep import QUALITY_LABELS, format_sleep_status
from states.forms import SleepInput

router = Router()

_QUICK_HOURS = [4, 5, 6, 7, 8, 9, 10]
_HISTORY_LIMIT = 7


def _sleep_keyboard():
    builder = InlineKeyboardBuilder()
    for h in _QUICK_HOURS:
        builder.button(text=f"{h}ч", callback_data=f"sleep_hours:{h}.0")
    builder.button(text="✏️ Другое", callback_data="sleep_custom")
    builder.adjust(4, 4)
    return builder.as_markup()


def _quality_keyboard():
    builder = InlineKeyboardBuilder()
    for score, label in QUALITY_LABELS.items():
        builder.button(text=label.capitalize(), callback_data=f"sleep_quality:{score}")
    builder.button(text="Пропустить", callback_data="sleep_quality:0")
    builder.adjust(3, 1)
    return builder.as_markup()


async def _ensure_user(src: Message | CallbackQuery):
    user = src.from_user
    await db.upsert_user(user.id, user.username or "", user.full_name or "")


async def _show_sleep(target: Message | CallbackQuery, user_id: int, edit: bool = False):
    rows = await db.get_sleep_history(user_id, _HISTORY_LIMIT)
    text = format_sleep_status(rows)
    kb = _sleep_keyboard()

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(text, reply_markup=kb)
        if isinstance(target, CallbackQuery):
            await target.answer()


@router.message(Command("sleep"))
@router.message(F.text == "😴 Сон")
async def cmd_sleep(message: Message):
    await _ensure_user(message)
    await _show_sleep(message, message.from_user.id)


@router.callback_query(F.data.startswith("sleep_hours:"))
async def cb_sleep_hours(callback: CallbackQuery, state: FSMContext):
    await _ensure_user(callback)
    try:
        hours = float(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Ошибка значения", show_alert=True)
        return
    await state.set_state(SleepInput.waiting_quality)
    await state.update_data(sleep_hours=hours)
    await callback.message.edit_text(
        f"Записываю {hours}ч сна.\n\nКак оцените качество?",
        reply_markup=_quality_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "sleep_custom")
async def cb_sleep_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SleepInput.waiting_hours)
    await callback.message.edit_text(
        "Введите количество часов сна (например: 6.5):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SleepInput.waiting_hours)
async def msg_sleep_hours(message: Message, state: FSMContext):
    await _ensure_user(message)
    value = (message.text or "").strip().replace(",", ".")
    try:
        hours = float(value)
    except ValueError:
        await message.answer("Введите число (например: 7 или 6.5).")
        return
    if hours < 1 or hours > 24:
        await message.answer("Укажите от 1 до 24 часов.")
        return
    await state.update_data(sleep_hours=hours)
    await state.set_state(SleepInput.waiting_quality)
    await message.answer(
        f"Записываю {hours}ч сна.\n\nКак оцените качество?",
        reply_markup=_quality_keyboard(),
    )


@router.callback_query(F.data.startswith("sleep_quality:"), SleepInput.waiting_quality)
async def cb_sleep_quality(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hours = data.get("sleep_hours", 0.0)
    quality_raw = callback.data.split(":")[1]
    quality = int(quality_raw) or None  # 0 → None (пропустить)

    await state.clear()
    sleep_date = date.today().isoformat()
    await db.log_sleep(callback.from_user.id, sleep_date, hours, quality)
    await _show_sleep(callback, callback.from_user.id, edit=True)
