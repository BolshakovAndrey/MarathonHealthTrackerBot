import asyncio
import sys

import sentry_sdk
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter

from config import settings
from loader import bot, dp, db, logger
from handlers import all_routers
from services.scheduler import setup_scheduler


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
        send_default_pii=True,
        before_send=_sentry_before_send,
    )
    logger.info("Sentry инициализирован")


@dp.error(ExceptionTypeFilter(TelegramBadRequest))
async def handle_bad_request(event: types.ErrorEvent):
    if "message is not modified" in str(event.exception):
        return True
    raise event.exception


@dp.error()
async def handle_unknown_error(event: types.ErrorEvent):
    """Fallback: логирует необработанные исключения и сообщает пользователю."""
    logger.exception("Необработанная ошибка: %s", event.exception)
    update = event.update
    message = None
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        try:
            await update.callback_query.answer()
        except Exception:
            pass
    if message:
        try:
            await message.answer(
                "⚠️ Произошла ошибка. Попробуйте ещё раз или нажмите /start."
            )
        except Exception:
            pass
    return True


_scheduler = None


async def on_startup():
    global _scheduler
    await db.connect()
    logger.info(f"БД подключена (postgres={db._use_pg})")
    _scheduler = setup_scheduler(bot)
    _scheduler.start()
    logger.info("Планировщик запущен")


async def on_shutdown():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Планировщик остановлен")
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
