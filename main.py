import asyncio
import logging
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import router, sync_admins
from scheduler import start_scheduler, scheduler


async def main():
    logging.basicConfig(level=logging.INFO)

    # 1. SQLite ma'lumotlar bazasini ishga tushirish
    await init_db()
    await sync_admins()

    # 2. Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()
    dp.include_router(router)

    # 3. Har oylik avtomatik eslatmalar jadvalini ishga tushirish
    start_scheduler(bot)

    print("🚀 Piramida O‘quv Markazi boti muvaffaqiyatli ishga tushdi!")

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if scheduler.running:
            try:
                scheduler.shutdown(wait=False)
            except Exception:
                pass
        try:
            await bot.session.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to‘xtatildi.")