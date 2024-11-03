import os
import requests
from abc import ABC
from bs4 import BeautifulSoup
from bot_app.exceptions import HTMLBlockNotFound, HTMLError
from bot_app.consts import PARSER_NEWS_ID_DIR
from bot_app.log import logger


class AbstractParser(ABC):
    __name__ = ''
    URL = ''

    def __init__(self) -> None:
        self.last_news_item_id = None
        os.makedirs(f'{PARSER_NEWS_ID_DIR}', exist_ok=True)
        self.filepath = os.path.abspath(f'{PARSER_NEWS_ID_DIR}/{self.__name__}')
        if not os.path.exists(self.filepath):
            logger.info(f'Creating file {self.filepath} for {self.__name__}')
            with open(self.filepath, 'w+') as f:
                f.close()
        logger.info(f'Initialized parser for {self.__name__}, file path: {self.filepath}')

    def get_last_news_item_from_url(self) -> dict:
        """
        return: {
                    'id': str,
                    'title': str,
                    'link': str
                }
        """
        raise NotImplementedError

    def store_last_news_item_id(self, id):
        logger.info(f'Storing last news item ID: {id}')
        with open(self.filepath, 'w') as file:
            file.write(str(id))

    def read_last_news_item_id(self):
        logger.info(f'Reading old id from {self.filepath}')
        with open(self.filepath, 'r') as file:
            old_id = file.read()
        logger.info(f'Last news item ID retrieved: {old_id}')
        return old_id

    def renew_flag(self, old_id, new_id):
        if type(old_id) is not type(new_id):
            old_id = str(old_id)
            new_id = str(new_id)
        if not old_id or old_id != new_id:
            return True
        return False

    def get_last_news_object(self):
        result = self.get_last_news_item_from_url()
        new_id = result['id']
        old_id = self.read_last_news_item_id()

        if self.renew_flag(old_id, new_id):
            self.store_last_news_item_id(new_id)
            logger.info(f'New news item found. ID: {new_id}, Title: {result["title"]}')
            return result
        else:
            logger.info(f'No new news item found. Current ID: {old_id}, New ID: {new_id}')


class RBCParser(AbstractParser):
    __name__ = 'rbc_parser'
    URL = 'https://www.rbc.ru/crypto/?utm_source=topline'

    def get_last_news_item_from_url(self):
        logger.info(f'Fetching last news item from URL: {self.URL}')
        try:
            resp = requests.get(self.URL)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                lookup_class = 'item js-rm-central-column-item'
                logger.info(f'Successfully fetched data from {self.URL}')

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

                    logger.debug(f'Found news item - ID: {news_id}, Title: {title}, Link: {link}')

                    return {
                        'id': news_id,
                        'title': title,
                        'link': link
                    }
                else:
                    logger.error(f'HTML Block Not Found: {lookup_class}')
                    raise HTMLBlockNotFound(f'{lookup_class}')

            else:
                logger.error(f'HTTP Error: {self.URL} returned status code {resp.status_code}')
                raise HTMLError(f'{self.URL}: {resp.status_code}')
        except Exception as e:
            logger.exception('An error occurred while fetching news item from URL: {}'.format(str(e)))
            raise
