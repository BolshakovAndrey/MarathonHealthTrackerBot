from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from keyboards.inline_keyboards import main_menu_keyboard, cancel_keyboard
from services.kbju import calculate_kbju
from states.forms import ProfileSetup

router = Router()


def _gender_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👨 Мужской", callback_data="gender:male")
    builder.button(text="👩 Женский", callback_data="gender:female")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def _activity_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛋️ Минимальная", callback_data="activity:sedentary")
    builder.button(text="🚶 Легкая", callback_data="activity:light")
    builder.button(text="🏃 Средняя", callback_data="activity:moderate")
    builder.button(text="🏋️ Высокая", callback_data="activity:high")
    builder.button(text="🔥 Очень высокая", callback_data="activity:very_high")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def _goal_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📉 Похудение", callback_data="goal:lose")
    builder.button(text="⚖️ Поддержание", callback_data="goal:maintain")
    builder.button(text="📈 Набор", callback_data="goal:gain")
    builder.button(text="🚫 Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


async def _start_profile_setup(target: Message | CallbackQuery, state: FSMContext):
    text = (
        "🧮 <b>Настройка профиля</b>\n\n"
        "Шаг 1/6. Выберите пол:"
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=_gender_keyboard())
        await target.answer()
    else:
        await target.answer(text, reply_markup=_gender_keyboard())
    await state.set_state(ProfileSetup.waiting_gender)


@router.callback_query(F.data == "profile_setup_start")
async def cb_profile_setup_start(callback: CallbackQuery, state: FSMContext):
    await _start_profile_setup(callback, state)


@router.message(F.text == "⚙️ Профиль")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = message.from_user
    if user is None:
        return

    row = await db.get_user(user.id)
    if not row or row[3] is None:
        text = (
            "Профиль пока не заполнен.\n\n"
            "Нажмите кнопку ниже, чтобы начать настройку."
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🧮 Настроить профиль", callback_data="profile_setup_start")
        await message.answer(text, reply_markup=builder.as_markup())
        return

    gender = "Мужской" if row[3] == "male" else "Женский"
    text = (
        "📊 <b>Ваш профиль</b>\n\n"
        f"Пол: <b>{gender}</b>\n"
        f"Возраст: <b>{row[4]}</b>\n"
        f"Рост: <b>{row[5]} см</b>\n"
        f"Вес: <b>{row[6]} кг</b>\n"
        f"Активность: <b>{row[7]}</b>\n"
        f"Цель: <b>{row[8]}</b>\n\n"
        "🍽️ <b>КБЖУ</b>\n"
        f"BMR: <b>{round(row[9], 1)}</b>\n"
        f"TDEE: <b>{round(row[10], 1)}</b>\n"
        f"Калории: <b>{row[11]} ккал</b>\n"
        f"Белки: <b>{row[12]} г</b>\n"
        f"Жиры: <b>{row[13]} г</b>\n"
        f"Углеводы: <b>{row[14]} г</b>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Пересчитать профиль", callback_data="profile_setup_start")
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Настройка отменена.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(ProfileSetup.waiting_gender, F.data.startswith("gender:"))
async def cb_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":", 1)[1]
    await state.update_data(gender=gender)
    await state.set_state(ProfileSetup.waiting_age)
    await callback.message.edit_text("Шаг 2/6. Введите возраст (10-100):", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(ProfileSetup.waiting_age)
async def msg_age(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("Введите возраст числом (10-100).")
        return
    age = int(value)
    if age < 10 or age > 100:
        await message.answer("Возраст должен быть от 10 до 100.")
        return
    await state.update_data(age=age)
    await state.set_state(ProfileSetup.waiting_height)
    await message.answer("Шаг 3/6. Введите рост (см, 100-250):", reply_markup=cancel_keyboard())


@router.message(ProfileSetup.waiting_height)
async def msg_height(message: Message, state: FSMContext):
    value = (message.text or "").strip().replace(",", ".")
    try:
        height = float(value)
    except ValueError:
        await message.answer("Введите рост числом (например, 170).")
        return
    if height < 100 or height > 250:
        await message.answer("Рост должен быть от 100 до 250 см.")
        return
    await state.update_data(height=height)
    await state.set_state(ProfileSetup.waiting_weight)
    await message.answer("Шаг 4/6. Введите вес (кг, 30-300):", reply_markup=cancel_keyboard())


@router.message(ProfileSetup.waiting_weight)
async def msg_weight(message: Message, state: FSMContext):
    value = (message.text or "").strip().replace(",", ".")
    try:
        weight = float(value)
    except ValueError:
        await message.answer("Введите вес числом (например, 68.5).")
        return
    if weight < 30 or weight > 300:
        await message.answer("Вес должен быть от 30 до 300 кг.")
        return
    await state.update_data(weight=weight)
    await state.set_state(ProfileSetup.waiting_activity_level)
    await message.answer("Шаг 5/6. Выберите уровень активности:", reply_markup=_activity_keyboard())


@router.callback_query(ProfileSetup.waiting_activity_level, F.data.startswith("activity:"))
async def cb_activity(callback: CallbackQuery, state: FSMContext):
    activity = callback.data.split(":", 1)[1]
    await state.update_data(activity_level=activity)
    await state.set_state(ProfileSetup.waiting_goal)
    await callback.message.edit_text("Шаг 6/6. Выберите цель:", reply_markup=_goal_keyboard())
    await callback.answer()


@router.callback_query(ProfileSetup.waiting_goal, F.data.startswith("goal:"))
async def cb_goal(callback: CallbackQuery, state: FSMContext):
    goal = callback.data.split(":", 1)[1]
    data = await state.get_data()

    user = callback.from_user
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    username = user.username or ""
    full_name = (user.full_name or "").strip() or str(user.id)
    await db.upsert_user(user_id=user.id, username=username, full_name=full_name)

    result = calculate_kbju(
        gender=data["gender"],
        age=int(data["age"]),
        height_cm=float(data["height"]),
        weight_kg=float(data["weight"]),
        activity_level=data["activity_level"],
        goal=goal,
    )

    await db.update_profile(
        user_id=user.id,
        gender=data["gender"],
        age=int(data["age"]),
        height=float(data["height"]),
        weight=float(data["weight"]),
        activity_level=data["activity_level"],
        goal=goal,
        bmr=result.bmr,
        tdee=result.tdee,
        calories=result.calories,
        protein=result.protein,
        fat=result.fat,
        carbs=result.carbs,
    )

    await state.clear()
    text = (
        "✅ <b>Профиль сохранен!</b>\n\n"
        "🍽️ <b>Ваши цели КБЖУ:</b>\n"
        f"BMR: <b>{result.bmr}</b>\n"
        f"TDEE: <b>{result.tdee}</b>\n"
        f"Калории: <b>{result.calories} ккал</b>\n"
        f"Белки: <b>{result.protein} г</b>\n"
        f"Жиры: <b>{result.fat} г</b>\n"
        f"Углеводы: <b>{result.carbs} г</b>"
    )
    await callback.message.edit_text(text)
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()
