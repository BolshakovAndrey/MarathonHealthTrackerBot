import asyncio
import sys

import sentry_sdk
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter

from config import settings
from loader import bot, dp, db, logger
from handlers import all_routers


def _sentry_before_send(event, hint):
    """Фильтрует шумные ошибки перед отправкой в Sentry."""
    if "exception" in event:
        for exc in event["exception"].get("values", []):
            exc_type = exc.get("type", "")
            exc_value = exc.get("value", "")
            combined = f"{exc_type}: {exc_value}".lower()

            if "bot was blocked by the user" in combined:
                return None
            if "chat not found" in combined:
                return None
            if "telegramnetworkerror" in exc_type.lower():
                return None
            if "message is not modified" in exc_value.lower():
                return None

    text = f"{event.get('message', '')} {event.get('logentry', {}).get('message', '')}".lower()
    if any(s in text for s in ("bot was blocked", "failed to fetch updates", "connection reset")):
        return None

    return event


if settings.SENTRY_DSN and settings.is_production:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=settings.APP_ENV,
        before_send=_sentry_before_send,
    )
    logger.info("Sentry инициализирован")


@dp.error(ExceptionTypeFilter(TelegramBadRequest))
async def handle_bad_request(event: types.ErrorEvent):
    if "message is not modified" in str(event.exception):
        return True
    raise event.exception


async def on_startup():
    await db.connect()
    logger.info(f"БД подключена (postgres={db._use_pg})")


async def on_shutdown():
    await db.close()
    logger.info("БД отключена")


async def main():
    for router in all_routers:
        dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
        sys.exit(0)
