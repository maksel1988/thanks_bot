import os
from datetime import datetime, timedelta
from telegram import Update, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pytz
import psycopg2
from psycopg2 import sql
import csv
from io import StringIO
import pandas as pd

# Конфигурация
TOKEN = os.getenv('7683983088:AAFLJDWfegXb0YkJIGo2t8NAED1ED3xe2WU')
CHANNEL_ID = '@ad_thanks'
ADMIN_ID = 49952799

# Настройки PostgreSQL
DB_NAME = os.getenv('DB_NAME', 'thanks_bot')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS thanks (
                    id SERIAL PRIMARY KEY,
                    sender_id BIGINT,
                    sender_username TEXT,
                    message_text TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    id SERIAL PRIMARY KEY,
                    thanks_id INTEGER REFERENCES thanks(id),
                    username TEXT,
                    mentioned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monthly_winners (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    thanks_count INTEGER,
                    month INTEGER,
                    year INTEGER,
                    announced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            self.conn.commit()

    def add_thanks(self, sender_id, sender_username, message_text, mentions):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO thanks (sender_id, sender_username, message_text) VALUES (%s, %s, %s) RETURNING id",
                (sender_id, sender_username, message_text)
            )
            thanks_id = cur.fetchone()[0]
            
            for mention in mentions:
                cur.execute(
                    "INSERT INTO mentions (thanks_id, username) VALUES (%s, %s)",
                    (thanks_id, mention.lower())
                )
            
            self.conn.commit()
        return thanks_id

    def get_current_stats(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT username, COUNT(*) as count 
                FROM mentions 
                WHERE mentioned_at >= date_trunc('month', NOW())
                GROUP BY username 
                ORDER BY count DESC
            """)
            return cur.fetchall()

    def get_all_time_stats(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT username, COUNT(*) as count 
                FROM mentions 
                GROUP BY username 
                ORDER BY count DESC
            """)
            return cur.fetchall()

    def get_monthly_winners(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT username, thanks_count, month, year 
                FROM monthly_winners 
                ORDER BY year DESC, month DESC
            """)
            return cur.fetchall()

    def add_monthly_winner(self, username, count):
        now = datetime.now()
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO monthly_winners (username, thanks_count, month, year)
                VALUES (%s, %s, %s, %s)
            """, (username, count, now.month, now.year))
            self.conn.commit()

    def get_mentions_for_user(self, username):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT t.message_text, t.sender_username, m.mentioned_at
                FROM mentions m
                JOIN thanks t ON m.thanks_id = t.id
                WHERE m.username = %s
                ORDER BY m.mentioned_at DESC
            """, (username.lower(),))
            return cur.fetchall()

    def get_data_for_export(self, start_date, end_date):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    m.username,
                    t.sender_username,
                    t.message_text,
                    m.mentioned_at
                FROM mentions m
                JOIN thanks t ON m.thanks_id = t.id
                WHERE m.mentioned_at BETWEEN %s AND %s
                ORDER BY m.mentioned_at DESC
            """, (start_date, end_date))
            return cur.fetchall()

db = Database()
bot = Bot(token=TOKEN)

def notify_user(username, sender_username, message_text):
    try:
        message = (
            f"🎉 Вас поблагодарили!\n\n"
            f"От: @{sender_username}\n"
            f"Сообщение: {message_text}\n\n"
            f"Спасибо за ваш вклад!"
        )
        bot.send_message(
            chat_id=username,  # Для username нужно использовать @username
            text=message
        )
    except Exception as e:
        print(f"Ошибка при отправке уведомления {username}: {e}")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Отправьте благодарность в формате:\n"
        "@username1 @username2 Текст благодарности\n\n"
        "Бот отправит сообщение в канал и учтет статистику."
    )

def handle_thanks(update: Update, context: CallbackContext):
    text = update.message.text
    words = text.split()
    
    mentions = []
    i = 0
    while i < len(words) and words[i].startswith('@'):
        mentions.append(words[i])
        i += 1
    
    if not mentions:
        update.message.reply_text("Не найдены упоминания аккаунтов в начале сообщения!")
        return
    
    gratitude_text = ' '.join(words[i:])
    if not gratitude_text:
        update.message.reply_text("Пожалуйста, добавьте текст благодарности!")
        return
    
    # Сохраняем в базу
    sender = update.effective_user
    thanks_id = db.add_thanks(sender.id, sender.username, gratitude_text, mentions)
    
    # Отправляем в канал
    message = f"{' '.join(mentions)}\n\n{gratitude_text}\n\n#благодарности"
    context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Отправляем уведомления
    for mention in mentions:
        notify_user(mention, sender.username, gratitude_text)
    
    update.message.reply_text("Благодарность отправлена в канал и учтена в статистике!")

def export_data(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("Эта команда только для администратора!")
        return
    
    try:
        # Парсим аргументы (формат: /export 2023-01-01 2023-12-31)
        args = context.args
        if len(args) != 2:
            update.message.reply_text("Использование: /export ГГГГ-ММ-ДД ГГГГ-ММ-ДД")
            return
        
        start_date = datetime.strptime(args[0], "%Y-%m-%d")
        end_date = datetime.strptime(args[1], "%Y-%m-%d")
        
        # Получаем данные
        data = db.get_data_for_export(start_date, end_date)
        
        if not data:
            update.message.reply_text("Нет данных за указанный период")
            return
        
        # Создаем CSV
        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(['Кому', 'От кого', 'Текст', 'Дата'])
        
        for row in data:
            writer.writerow(row)
        
        csv_file.seek(0)
        
        # Отправляем файл
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=csv_file,
            filename=f"thanks_export_{args[0]}_{args[1]}.csv"
        )
        
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("export", export_data))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_thanks))
    
    job_queue = updater.job_queue
    job_queue.run_monthly(
        announce_winner,
        when=datetime.now(pytz.utc).replace(day=1, hour=0, minute=0) + timedelta(days=32),
        day=1,
        time=datetime.time(hour=0, minute=0)
    )
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
