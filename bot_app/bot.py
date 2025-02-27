import os

import time
import threading
from typing import List

import telebot
from telebot import formatting
from dotenv import load_dotenv, set_key

from bot_app.log import logger
from bot_app.parsers import AbstractParser
from bot_app.scraping.parsers import InvestingParserSelenium
# from bot_app.parsers import RBCParser
from bot_app.consts import PERIOD


load_dotenv()

for env_var_name in ['TOKEN', 'CHANNEL_ID']:
    if not os.getenv(env_var_name):
        value = input(f'Введите {env_var_name}: ')
        os.environ.setdefault(env_var_name, value)
        set_key('.env', env_var_name, value)

TOKEN = os.getenv('TOKEN')  # Ваш токен
CHANNEL_ID = os.getenv('CHANNEL_ID')    # Ваш логин канала


class NewsParser:
    def __init__(self, parsers: List[AbstractParser]):
        self.thread: threading.Thread = None
        self.start_ts = None
        self.parsers = parsers

    def parse_news(self, delay: int):
        logger.info("Delaying parse_news for {}".format(delay))
        time.sleep(delay)
        while self.is_running:
            for parser in self.parsers:
                parser.get_last_news_object()

                if not parser.deque:
                    logger.info('No news object, skipping cycle')
                    continue

                copied_deque = parser.deque.copy()
                news_object: dict = copied_deque.popleft()
                if not news_object:
                    logger.info('news object пустой, скип')
                    continue

                raw_text = parser.get_article_text_selenium(news_object['link'])
                if not raw_text:
                    logger.error('Пустой текст статьи с {}'.format(news_object['link']))
                    continue
                article_text = formatting.escape_markdown(raw_text)

                if parser.deque:
                    try:
                        # сначала пытаемся запостить новость из очереди парсера
                        text = (
                            f'*{formatting.escape_markdown(news_object.get("title"))}*\n\n'
                            f'{article_text}\n'
                            f'[Читать продолжение в источнике]({news_object.get("link")})'
                        )
                        bot.send_message(
                            chat_id=CHANNEL_ID,
                            text=text,
                            parse_mode='MarkdownV2'
                        )

                        # если получилось, забираем её из очереди на постинг
                        parser.deque.popleft()
                        parser.cache.add(news_object.get('id'))
                        parser.store_last_news_item_id(news_object.get('id'))
                    except Exception as e:
                        logger.error('Exception on sending msg to channel: {}'.format(e))
            time.sleep(PERIOD)

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def start_thread(self, delay):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.parse_news, args=(delay,))
            self.thread.start()
            self.start_ts = time.monotonic()

    def stop_thread(self):
        # not working. Need event to handle thread stopping
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def delay(self):
        delay = 0
        current_ts = time.monotonic()
        if not self.start_ts:
            return delay
        if current_ts < self.start_ts + PERIOD:
            delay = PERIOD - (current_ts - self.start_ts)
        return delay


bot = telebot.TeleBot(TOKEN)
# rbc_parser = RBCParser()
investing_parser = InvestingParserSelenium()
news_parser_thread = NewsParser(
    [
        investing_parser,
        # rbc_parser
    ]
)


@bot.message_handler(content_types=['text'])
def commands(message):
    status_msg = ''

    if message.text == "/stop":
        if not news_parser_thread.is_running():
            status_msg += "Ошибка: парсинг не запущен."
        else:
            news_parser_thread.stop_thread()
            status_msg += "Остановка парсинга"
        bot.send_message(message.from_user.id, status_msg)
    elif message.text == "/start":
        delay = 0

        if news_parser_thread.is_running():
            status_msg += 'Ошибка: парсинг уже запущен'
        else:
            delay = news_parser_thread.delay()
            if delay > 0:
                status_msg += (
                    f'Старт парсинга отложен на {round(delay)} секунд, '
                    'т.к. он уже был запущен ранее.'
                )
            else:
                status_msg += 'Парсинг запущен'
            news_parser_thread.start_thread(delay)
        bot.send_message(message.from_user.id, status_msg)
    elif message.text == "/news_sources":
        news_parser_threads_info = '\n'.join(
            [f'{x.__name__}: {x.URL}' for x in news_parser_thread.parsers]
        )
        bot.send_message(
            message.from_user.id,
            f'Текущие источники новостей:\n{news_parser_threads_info}'
        )
    elif message.text == '/status':
        if news_parser_thread.is_running():
            ts = time.monotonic() - news_parser_thread.start_ts
            time_str = '{}min {}sec'.format(int(ts // 60), int(ts % 60))
            bot.send_message(
                message.from_user.id,
                "Парсинг запущен {}  назад.".format(time_str)
            )
        else:
            bot.send_message(message.from_user.id, "Парсинг остановлен.")
    elif message.text == '/help':
        bot.send_message(
            message.from_user.id,
            "cmds: /start, /stop, /status, /news_sources"
        )
    else:
        bot.send_message(
            message.from_user.id, "Я тебя не понимаю. Напиши '/help'."
        )
