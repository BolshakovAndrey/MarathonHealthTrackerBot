from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import cancel_keyboard
from services.water import calc_default_goal, format_water_status, week_dates
from states.forms import WaterInput

router = Router()

QUICK_AMOUNTS = [250, 500, 1000]


def _water_keyboard(goal_ml: int):
    builder = InlineKeyboardBuilder()
    for ml in QUICK_AMOUNTS:
        builder.button(text=f"+{ml} мл", callback_data=f"water_add:{ml}")
    builder.button(text="✏️ Другое", callback_data="water_custom")
    builder.button(text="🎯 Цель", callback_data="water_set_goal")
    builder.adjust(3, 2)
    return builder.as_markup()


async def _get_goal(user_id: int) -> int:
    """Получает цель из профиля или рассчитывает дефолт."""
    saved = await db.get_water_goal(user_id)
    if saved:
        return saved
    row = await db.get_user(user_id)
    # row: (user_id, username, full_name, gender, age, height, weight, ...)
    gender = row[3] if row else None
    weight = row[6] if row else None
    return calc_default_goal(gender, weight)


async def _show_water(target: Message | CallbackQuery, user_id: int, edit: bool = False):
    today = date.today().isoformat()
    current = await db.get_water_today(user_id, today)
    goal = await _get_goal(user_id)
    dates = week_dates()
    week = await db.get_water_week(user_id, dates)

    text = format_water_status(current, goal, week)
    kb = _water_keyboard(goal)

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(text, reply_markup=kb)
        if isinstance(target, CallbackQuery):
            await target.answer()


@router.message(Command("water"))
@router.message(F.text == "💧 Вода")
async def cmd_water(message: Message):
    await _show_water(message, message.from_user.id)


@router.callback_query(F.data.startswith("water_add:"))
async def cb_water_add(callback: CallbackQuery):
    ml = int(callback.data.split(":")[1])
    today = date.today().isoformat()
    await db.log_water(callback.from_user.id, ml)
    await _show_water(callback, callback.from_user.id, edit=True)


@router.callback_query(F.data == "water_custom")
async def cb_water_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WaterInput.waiting_amount)
    await callback.message.edit_text(
        "Введите количество воды в мл (например: 350):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(WaterInput.waiting_amount)
async def msg_water_amount(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("Введите целое число миллилитров.")
        return
    ml = int(value)
    if ml < 10 or ml > 5000:
        await message.answer("Укажите от 10 до 5000 мл.")
        return
    await state.clear()
    await db.log_water(message.from_user.id, ml)
    await _show_water(message, message.from_user.id)


@router.callback_query(F.data == "water_set_goal")
async def cb_water_set_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WaterInput.waiting_goal)
    current_goal = await _get_goal(callback.from_user.id)
    await callback.message.edit_text(
        f"Текущая цель: <b>{current_goal} мл</b>\n\n"
        "Введите новую цель в мл (1000–5000):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(WaterInput.waiting_goal)
async def msg_water_goal(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("Введите целое число миллилитров.")
        return
    goal = int(value)
    if goal < 1000 or goal > 5000:
        await message.answer("Цель должна быть от 1000 до 5000 мл.")
        return
    await state.clear()
    await db.set_water_goal(message.from_user.id, goal)
    await message.answer(f"✅ Цель установлена: <b>{goal} мл/день</b>")
    await _show_water(message, message.from_user.id)
