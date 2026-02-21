from aiogram import Router

from .start import router as start_router
from .profile import router as profile_router
from .water import router as water_router
from .mood import router as mood_router

all_routers: list[Router] = [
    start_router,
    profile_router,
    water_router,
    mood_router,
]
