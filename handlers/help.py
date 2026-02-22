from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.inline_keyboards import main_menu_keyboard

router = Router()

_HELP_TEXT = """
🤖 <b>Marathon Health Tracker</b>

<b>Команды:</b>
/start — начало работы
/profile — настройка профиля и КБЖУ
/water — трекинг воды
/mood — запись настроения
/sleep — трекинг сна
/headache — запись мигрени
/today — сводка за сегодня
/week — отчёт за неделю
/export — выгрузка данных (CSV)
/cancel — отмена текущего действия
/help — эта справка

<b>Кнопки меню:</b>
💧 Вода | 😊 Настроение | 😴 Сон | 🤕 Мигрень
📊 Статистика | ⚙️ Профиль
""".strip()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(_HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer(
            "Действие отменено.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(
            "Нет активного действия.",
            reply_markup=main_menu_keyboard(),
        )
