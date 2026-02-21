from aiogram.fsm.state import State, StatesGroup


class ProfileSetup(StatesGroup):
    waiting_gender = State()
    waiting_age = State()
    waiting_height = State()
    waiting_weight = State()
    waiting_activity_level = State()
    waiting_goal = State()


class WaterInput(StatesGroup):
    waiting_amount = State()
    waiting_goal = State()


class MoodInput(StatesGroup):
    waiting_note = State()


class SleepInput(StatesGroup):
    waiting_hours = State()    # для произвольного ввода
    waiting_quality = State()  # выбор качества после ввода часов


class HeadacheInput(StatesGroup):
    waiting_intensity = State()  # кнопки 1-10
    waiting_location = State()   # кнопки локализации
    waiting_triggers = State()   # мульти-выбор триггеров
    waiting_duration = State()   # кнопки или текст (минуты)
