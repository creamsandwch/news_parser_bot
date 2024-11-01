import os

import telebot
import time
from typing import List

from bot_app.parsers import AbstractParser, RBCParser

from dotenv import load_dotenv, set_key

rbc_parser = RBCParser()

NEWS_PARSERS: List[AbstractParser] = [
    rbc_parser,
]

load_dotenv()

for env_var_name in ['TOKEN', 'CHANNEL_ID']:
    if not os.getenv(env_var_name):
        value = input(f'Введите {env_var_name}: ')
        os.environ.setdefault(env_var_name, value)
        set_key('.env', env_var_name, value)

TOKEN = os.getenv('TOKEN')  # Ваш токен
CHANNEL_ID = os.getenv('CHANNEL_ID')    # Ваш логин канала

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(content_types=['text'])
def commands(message):
    try:
        if message.text == "старт":
            while True:
                news_parsers_info = '\n'.join(
                    [f'{x.__name__}: {x.URL}' for x in NEWS_PARSERS]
                )
                bot.send_message(
                    message.from_user.id,
                    text=f'Парсинг источников: {news_parsers_info}'
                )
                for parser in NEWS_PARSERS:
                    news_object: dict = parser.get_last_news_object()
                    if news_object is not None:
                        bot.send_message(
                            chat_id=CHANNEL_ID,
                            text='{}\n{}'.format(
                                news_object.get('title'),
                                news_object.get('link')
                            )
                        )
                    time.sleep(1800)
        else:
            bot.send_message(
                message.from_user.id,
                "Я тебя не понимаю. Напиши 'старт'"
            )
    except Exception as e:
        bot.send_message(
            message.from_user.id,
            'Ошибка: {}'.format(str(e))
        )
