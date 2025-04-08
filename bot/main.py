import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import Config
from .handlers import common, thanks

logging.basicConfig(level=logging.INFO)

bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def on_startup(dp):
    await bot.send_message(Config.ADMIN_ID, "Бот запущен")

async def on_shutdown(dp):
    await bot.send_message(Config.ADMIN_ID, "Бот остановлен")
    await dp.storage.close()
    await dp.storage.wait_closed()

def setup_handlers():
    dp.register_message_handler(common.cmd_start, commands=["start"])
    dp.register_message_handler(thanks.process_thanks_message, content_types=types.ContentType.TEXT)

def main():
    setup_handlers()
    
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == '__main__':
    main()
