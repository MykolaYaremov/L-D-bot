import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# Імпорти роутерів
from handlers import common, courses, faq


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # --- ПОРЯДОК ВАЖЛИВИЙ ---
    # Спочатку специфічні фільтри
    dp.include_router(courses.router)
    dp.include_router(faq.router)

    # В кінці - загальні (де є Fallback і Main Menu)
    dp.include_router(common.router)

    print("✅ Бот запущено!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        # Це допоможе, якщо Windows плутає шляхи
        sys.path.append(".")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот зупинений.")