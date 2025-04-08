import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from config import Config
from ..services.db import get_db
from ..models.thanks import ThanksMessage

async def process_thanks_message(message: types.Message):
    # Проверяем формат сообщения
    text = message.text
    if not text:
        await message.reply("Пожалуйста, отправьте текстовое сообщение.")
        return
    
    # Ищем упоминания пользователей в начале сообщения
    mentions = re.findall(r'@\w+', text)
    if not mentions:
        await message.reply("Пожалуйста, укажите @username пользователей, которым хотите выразить благодарность, в начале сообщения.")
        return
    
    # Извлекаем текст благодарности
    thanks_text = re.sub(r'^(@\w+\s*)+', '', text).strip()
    if not thanks_text:
        await message.reply("Пожалуйста, добавьте текст благодарности после упоминаний пользователей.")
        return
    
    # Сохраняем в базу данных
    db = next(get_db())
    db_message = ThanksMessage(
        sender_id=message.from_user.id,
        sender_username=message.from_user.username,
        receiver_usernames=' '.join(mentions),
        message_text=thanks_text
    )
    db.add(db_message)
    db.commit()
    
    # Отправляем в канал
    formatted_message = f"{' '.join(mentions)}\n\n{thanks_text}\n\nОт: @{message.from_user.username}"
    await message.bot.send_message(Config.CHANNEL_ID, formatted_message)
    
    await message.reply("Ваша благодарность отправлена! Спасибо!")
