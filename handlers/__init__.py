from aiogram import Router

from .start import router as start_router
from .profile import router as profile_router

all_routers: list[Router] = [
    start_router,
    profile_router,
]
