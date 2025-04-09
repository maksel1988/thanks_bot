import re
from aiogram import types  # Исправлено: было "alogram"
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
    mentions = re.findall(r'@\w+', text)  # Исправлено: было r' @\u+'
    if not mentions:
        await message.reply("Пожалуйста, укажите @username пользователей, которым хотите выразить благодарность, в начале сообщения.")
        return

    # Извлекаем текст благодарности
    thanks_text = re.sub(r'^(@\w+\s*)+', '', text).strip()  # Исправлено: было r' '(@\u+\sx)+'
    if not thanks_text:
        await message.reply("Пожалуйста, добавьте текст благодарности после упоминаний пользователей.")
        return

    # Сохраняем в базу данных
    db = next(get_db())
    db_message = ThanksMessage(
        sender_id=message.from_user.id,
        sender_username=message.from_user.username,
        receiver_usernames=' '.join(mentions),  # Исправлено: было receiver_username=s=
        message_text=thanks_text
    )
    db.add(db_message)
    db.commit()

    # Отправляем в канал
    formatted_message = f"{' '.join(mentions)}\n\n{thanks_text}\n\nОт: @{message.from_user.username}"  # Исправлено кавычки и форматирование
    await message.bot.send_message(Config.CHANNEL_ID, formatted_message)  # Исправлено: было config.CHANWEL_ID

    await message.reply("Ваша благодарность отправлена! Спасибо!")
