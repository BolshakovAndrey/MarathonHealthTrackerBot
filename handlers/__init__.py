from aiogram import Router

from .start import router as start_router
from .profile import router as profile_router
from .water import router as water_router
from .mood import router as mood_router
from .sleep import router as sleep_router
from .headache import router as headache_router
from .stats import router as stats_router
from .help import router as help_router

all_routers: list[Router] = [
    start_router,
    profile_router,
    water_router,
    mood_router,
    sleep_router,
    headache_router,
    stats_router,
    help_router,
]
