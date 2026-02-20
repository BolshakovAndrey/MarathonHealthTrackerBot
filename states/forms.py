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
