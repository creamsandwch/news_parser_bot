import os
import requests
import logging
from abc import ABC
from bs4 import BeautifulSoup
from bot_app.exceptions import HTMLBlockNotFound, HTMLError
from bot_app.consts import PARSER_NEWS_ID_DIR

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)


class AbstractParser(ABC):
    __name__ = ''

    def __init__(self) -> None:
        self.last_news_item_id = None
        os.makedirs(f'{os.curdir}/{PARSER_NEWS_ID_DIR}', exist_ok=True)
        self.filepath = f'{os.curdir}/{PARSER_NEWS_ID_DIR}/{self.__name__}'
        with open(self.filepath, 'w+') as f:
            f.close()
        logging.info(f'Initialized parser for {self.__name__}, file path: {self.filepath}')

    def get_last_news_item_from_url(self) -> dict:
        raise NotImplementedError

    def store_last_news_item_id(self, id):
        logging.info(f'Storing last news item ID: {id}')
        with open(self.filepath, 'w') as file:
            file.write(id)

    def read_last_news_item_id(self):
        with open(self.filepath, 'r') as file:
            old_id = file.read()
        logging.info(f'Last news item ID retrieved: {old_id}')
        return old_id

    def get_last_news_object(self):
        result = self.get_last_news_item_from_url()
        new_id = result['id']
        old_id = self.read_last_news_item_id()

        if not old_id or old_id != new_id:
            self.store_last_news_item_id(new_id)
            logging.info(f'New news item found. ID: {new_id}, Title: {result["title"]}')
            return result
        else:
            logging.info(f'No new news item found. Current ID: {old_id}, New ID: {new_id}')


class RBCParser(AbstractParser):
    __name__ = 'rbc_parser'
    URL = 'https://www.rbc.ru/crypto/?utm_source=topline'

    def get_last_news_item_from_url(self):
        logging.info(f'Fetching last news item from URL: {self.URL}')
        try:
            resp = requests.get(self.URL)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                lookup_class = 'item js-rm-central-column-item'
                logging.info(f'Successfully fetched data from {self.URL}')

                # Находим блок новости
                news_item = soup.find(
                    'div',
                    class_='item js-rm-central-column-item item_big item_with-photo js-index-exclude'
                )
                if news_item:
                    # Получаем заголовок
                    title = news_item.find(
                        'span',
                        class_='item__title rm-cm-item-text js-rm-central-column-item-text'
                    ).get_text(strip=True)

                    # Получаем ссылку
                    link = news_item.find(
                        'a',
                        class_='item__link rm-cm-item-link js-rm-central-column-item-link'
                    )['href']

                    # Получаем id новости
                    news_id = news_item['data-id']

                    logging.debug(f'Found news item - ID: {news_id}, Title: {title}, Link: {link}')

                    return {
                        'id': news_id,
                        'title': title,
                        'link': link
                    }
                else:
                    logging.error(f'HTML Block Not Found: {lookup_class}')
                    raise HTMLBlockNotFound(f'{lookup_class}')

            else:
                logging.error(f'HTTP Error: {self.URL} returned status code {resp.status_code}')
                raise HTMLError(f'{self.URL}: {resp.status_code}')
        except Exception as e:
            logging.exception('An error occurred while fetching news item from URL: {}'.format(str(e)))
            raise
