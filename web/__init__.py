from flask import Flask
from bot.services.db import Base, engine

app = Flask(__name__)

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

from . import views
