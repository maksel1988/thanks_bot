from aiogram import types
from config import Config

async def cmd_start(message: types.Message):
    welcome_text = """
    Привет! Я бот для отправки благодарностей коллегам.

    Чтобы отправить благодарность, напиши сообщение в формате:
    @username1 @username2 Текст вашей благодарности...

    Пример:
    @ivan @anna Спасибо за помощь с проектом! Вы молодцы!
    """
    await message.answer(welcome_text)
