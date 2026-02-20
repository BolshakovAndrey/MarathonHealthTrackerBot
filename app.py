import asyncio
import sys

from loader import bot, dp, db, logger
from handlers import all_routers


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
