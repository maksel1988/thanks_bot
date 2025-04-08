import re

def parse_usernames(text: str):
    """Извлекает упоминания пользователей из текста"""
    usernames = re.findall(r'@\w+', text)
    return usernames

def format_thanks_message(sender: str, receivers: list, message: str):
    """Форматирует сообщение благодарности для канала"""
    return f"{' '.join(receivers)}\n\n{message}\n\nОт: @{sender}"
