from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import cancel_keyboard
from services.headache import (
    DURATIONS, LOCATIONS, TRIGGERS,
    format_headache_status, triggers_to_str,
)
from states.forms import HeadacheInput

router = Router()

_HISTORY_LIMIT = 10


# --- Клавиатуры ---

def _start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Записать эпизод", callback_data="hd_start")
    return builder.as_markup()


def _intensity_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"hd_intensity:{i}")
    builder.adjust(5)
    return builder.as_markup()


def _location_keyboard():
    builder = InlineKeyboardBuilder()
    for key, label in LOCATIONS:
        builder.button(text=label, callback_data=f"hd_location:{key}")
    builder.adjust(2)
    builder.row()
    builder.button(text="Пропустить", callback_data="hd_location:skip")
    return builder.as_markup()


def _triggers_keyboard(selected: list[str]):
    builder = InlineKeyboardBuilder()
    for key, label in TRIGGERS:
        prefix = "✓ " if key in selected else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"hd_trigger:{key}")
    builder.adjust(2)
    builder.row()
    builder.button(text="✅ Готово", callback_data="hd_triggers_done")
    builder.button(text="Пропустить", callback_data="hd_triggers_skip")
    return builder.as_markup()


def _duration_keyboard():
    builder = InlineKeyboardBuilder()
    for minutes, label in DURATIONS:
        builder.button(text=label, callback_data=f"hd_duration:{minutes}")
    builder.adjust(3)
    builder.row()
    builder.button(text="✏️ Другое", callback_data="hd_duration_custom")
    builder.button(text="Пропустить", callback_data="hd_duration:0")
    return builder.as_markup()


# --- Helpers ---

async def _ensure_user(src: Message | CallbackQuery):
    user = src.from_user
    await db.upsert_user(user.id, user.username or "", user.full_name or "")


async def _show_headache(target: Message | CallbackQuery, user_id: int, edit: bool = False):
    rows = await db.get_headache_history(user_id, _HISTORY_LIMIT)
    text = format_headache_status(rows)
    kb = _start_keyboard()

    if edit and isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(text, reply_markup=kb)
        if isinstance(target, CallbackQuery):
            await target.answer()


async def _save_and_show(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    user_id = callback.from_user.id
    await db.log_headache(
        user_id=user_id,
        intensity=data["intensity"],
        location=data.get("location"),
        triggers=triggers_to_str(data.get("triggers", [])),
        duration=data.get("duration") or None,
    )
    await _show_headache(callback, user_id, edit=True)


# --- Handlers ---

@router.message(Command("headache"))
@router.message(F.text == "🤕 Мигрень")
async def cmd_headache(message: Message):
    await _ensure_user(message)
    await _show_headache(message, message.from_user.id)


@router.callback_query(F.data == "hd_start")
async def cb_hd_start(callback: CallbackQuery, state: FSMContext):
    await _ensure_user(callback)
    await state.set_state(HeadacheInput.waiting_intensity)
    await callback.message.edit_text(
        "🤕 <b>Шаг 1/4 — Интенсивность</b>\n\nОцените боль от 1 (слабая) до 10 (невыносимая):",
        reply_markup=_intensity_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hd_intensity:"), HeadacheInput.waiting_intensity)
async def cb_hd_intensity(callback: CallbackQuery, state: FSMContext):
    intensity = int(callback.data.split(":")[1])
    await state.update_data(intensity=intensity)
    await state.set_state(HeadacheInput.waiting_location)
    await callback.message.edit_text(
        f"Интенсивность: <b>{intensity}/10</b>\n\n"
        "📍 <b>Шаг 2/4 — Локализация</b>\n\nГде болит?",
        reply_markup=_location_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hd_location:"), HeadacheInput.waiting_location)
async def cb_hd_location(callback: CallbackQuery, state: FSMContext):
    location_raw = callback.data.split(":")[1]
    location = None if location_raw == "skip" else location_raw
    await state.update_data(location=location, triggers=[])
    await state.set_state(HeadacheInput.waiting_triggers)
    data = await state.get_data()
    await callback.message.edit_text(
        "⚡ <b>Шаг 3/4 — Триггеры</b>\n\nВыберите один или несколько (можно не выбирать):",
        reply_markup=_triggers_keyboard(data.get("triggers", [])),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hd_trigger:"), HeadacheInput.waiting_triggers)
async def cb_hd_trigger_toggle(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    data = await state.get_data()
    selected: list[str] = list(data.get("triggers", []))
    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)
    await state.update_data(triggers=selected)
    await callback.message.edit_reply_markup(reply_markup=_triggers_keyboard(selected))
    await callback.answer()


@router.callback_query(
    F.data.in_({"hd_triggers_done", "hd_triggers_skip"}),
    HeadacheInput.waiting_triggers,
)
async def cb_hd_triggers_confirm(callback: CallbackQuery, state: FSMContext):
    await state.set_state(HeadacheInput.waiting_duration)
    await callback.message.edit_text(
        "⏱ <b>Шаг 4/4 — Длительность</b>\n\nСколько длилась боль?",
        reply_markup=_duration_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hd_duration:"), HeadacheInput.waiting_duration)
async def cb_hd_duration(callback: CallbackQuery, state: FSMContext):
    minutes_raw = int(callback.data.split(":")[1])
    await state.update_data(duration=minutes_raw if minutes_raw > 0 else None)
    await _save_and_show(callback, state)


@router.callback_query(F.data == "hd_duration_custom", HeadacheInput.waiting_duration)
async def cb_hd_duration_custom(callback: CallbackQuery, state: FSMContext):
    # Остаёмся в waiting_duration, но переходим к текстовому вводу
    await state.update_data(duration_custom=True)
    await callback.message.edit_text(
        "Введите длительность в минутах (1–1440):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(HeadacheInput.waiting_duration)
async def msg_hd_duration_custom(message: Message, state: FSMContext):
    await _ensure_user(message)
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("Введите целое число минут (например: 45).")
        return
    minutes = int(value)
    if minutes < 1 or minutes > 1440:
        await message.answer("Укажите от 1 до 1440 минут (24 часа).")
        return
    data = await state.get_data()
    await state.update_data(duration=minutes)

    # Сохраняем через прямой вызов DB (нет callback объекта)
    await state.clear()
    await db.log_headache(
        user_id=message.from_user.id,
        intensity=data["intensity"],
        location=data.get("location"),
        triggers=triggers_to_str(data.get("triggers", [])),
        duration=minutes,
    )
    rows = await db.get_headache_history(message.from_user.id, _HISTORY_LIMIT)
    text = format_headache_status(rows)
    await message.answer(text, reply_markup=_start_keyboard())
