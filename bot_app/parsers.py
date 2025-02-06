import os
import json
import time
import requests
from urllib.parse import urlparse
from abc import ABC
from collections import deque

from bs4 import BeautifulSoup
from lxml import html

from bot_app.exceptions import HTMLBlockNotFound, HTMLError
from bot_app.consts import PARSER_NEWS_ID_DIR, PERIOD
from bot_app.log import logger


class AbstractParser(ABC):
    __name__ = ''
    URL = ''

    def __init__(self) -> None:
        self.cache = set()
        self.deque = deque()
        self.start_ts = None
        self.last_news_item_id = None
        os.makedirs(f'{PARSER_NEWS_ID_DIR}', exist_ok=True)
        self.filepath = os.path.abspath(
            f'{PARSER_NEWS_ID_DIR}/{self.__name__}'
        )
        if not os.path.exists(self.filepath):
            logger.info(f'Creating file {self.filepath} for {self.__name__}')
            with open(self.filepath, 'w+') as f:
                f.close()
        logger.info(
            (
                f'Initialized parser for {self.__name__},'
                f'file path: {self.filepath}'
            )
        )

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
        if (not old_id or old_id != new_id) and new_id not in self.cache:
            return True
        return False

    def get_last_news_object(self):
        current_ts = time.monotonic()
        if not (self.start_ts is None or current_ts > self.start_ts + PERIOD):
            return

        try:
            result = self.get_last_news_item_from_url()
        except Exception as e:
            logger.error(
                'Error on fetching latest news: {} on URL: {}'.format(
                    e, self.URL
                )
            )
            return

        if not result:
            return

        self.start_ts = current_ts
        new_id = result['id']
        old_id = self.read_last_news_item_id()

        if self.renew_flag(old_id, new_id):
            self.deque.append(result)
            logger.info(f'New news item found. ID: {new_id}, Title: {result["title"]}')
        else:
            logger.info(f'No new news item found. Current ID: {old_id}, New ID: {new_id}')

    def get_article_text_selenium(self, newslink):
        pass


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


class InvestingParser(AbstractParser):
    __name__ = 'investing.com_parser'
    URL = 'https://ru.investing.com/news/most-popular-news'

    def get_last_news_item_from_url(self) -> dict:
        try:
            response = requests.get(self.URL)
        except Exception as e:
            logger.error(f'Ошибка при запросе: {e}')
            raise

        # Проверяем, успешен ли запрос
        if response.status_code == 200:
            # Предположим, что данные приходят в формате JSON
            html_content = response.text

            # Создаем объект BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Находим тег <script> с нужным id
            script_tag = soup.find('script', id='__NEXT_DATA__')

            # Проверяем, что тег найден
            if script_tag:
                # Загружаем JSON данные
                json_data = json.loads(script_tag.string)

                # Извлекаем нужную информацию
                breaking_news = json_data['props']['pageProps']['state']['newsStore']['_mostPopularNewsList']
                if type(breaking_news) is list:
                    news_item = breaking_news[0]
                    title = news_item.get('title')
                    link = news_item.get('href')
                    news_id = news_item.get('article_ID')
                    return {
                        'id': news_id,
                        'title': title,
                        'link': f'{urlparse(self.URL).scheme}://{urlparse(self.URL).netloc}{link}'
                    }
                else:
                    logger.error(
                        (
                            f'{__name__}: изменился формат'
                            f'данных на странице {self.URL}'
                        )
                    )                
                if title and link and news_id:
                    logger.debug(f'Found news item - ID: {id} title: {title} href {link}')
        else:
            raise Exception(
                'Status code on request != 200: {}'.format(
                    response.status_code
                )
            )


def get_article_text(newslink) -> str:
    try:
        headers = {
            "authority": "ru.investing.com",
            "method": "GET",
            "path": "/news/world-news/article-2633668",
            "scheme": "https",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8,und;q=0.7,fr;q=0.6",
            "cache-control": "max-age=0",
            "cookie": "udid=4139e5d64bf6dc91d3cd0133af055870; _ym_uid=1733296529744292446; _ym_d=1733296529; adBlockerNewUserDomains=1733296529; __eventn_id=4139e5d64bf6dc91d3cd0133af055870; _hjSessionUser_174945=eyJpZCI6ImM1OTRjYjUwLTc4YmUtNWZiOS1iYjU1LTY3MDhkYjViNTg0NiIsImNyZWF0ZWQiOjE3MzMyOTY1Mjk4ODIsImV4aXN0aW5nIjp0cnVlfQ==; _ga=GA1.1.1284488866.1733296530; _fbp=fb.1.1733388533166.404328690196952867; page_equity_viewed=0; invab=keysignup_0|ovads_1|propicks_1; __cflb=0H28vFEFimnpowq71CdWzBFhnnYdQ9p5uP2D2bckxNY; user-browser-sessions=4; browser-session-counted=true; _ym_isad=1; _hjSession_174945=eyJpZCI6IjdhOTBkYmJkLTE3MjUtNDFjMi1hMDFkLTQ2MTk2ZTEwNWEzZiIsImMiOjE3MzgwNjMxMzg5NTEsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; r_p_s_n=1; PHPSESSID=ia0ve4b2g9bs27cd7loo0g52or; geoC=RU; gtmFired=OK; reg_trk_ep=google%20one%20tap; adsFreeSalePopUp=2; gcc=RU; gsc=; __cf_bm=GaBgAi2mih7zjyBYWrQCOp3bNqGfwWuviY4Ct1RU6JQ-1738066813-1.0.1.1-AZl7Y2ppR4Z_cTncSmHmor_ymAVuDZz2en.1iT0.7P0ceTXDja6VgGVfYztnb1FVS3xi6PAonzpsSxgCRVuV7ybdmyDr40Bd.uktai07ldQ; invpc=7; page_view_count=7; lifetime_page_view_count=28; _hjHasCachedUserAttributes=true; cf_clearance=BTBWQVWBOpIhEDGXlObQb34hO.08PEauauGBh38Pwhs-1738066814-1.2.1.1-r4G8o0CuUWwh7dWoRfo.4d2C15NhpqGnORjFUWGoMBj.3Vcbftb3ao9rc9vboHRE.7oSwLPVoVDJScQPthUVeCRt3yW0Wx6NBsu4dFN5.b6qgPwXfSYlW4oShWFrrLON9sYTf7Edjtx1EUk4kiOLrmpq1B6xRWcJkvDMmVjq1rE6.c5WYa1BKQJrzBaLyRlyG1ClHgj39qnl7cm4yyO2MuJ_WKkHxaqN5obEaNhvcvDgJ8wSKSBxY2poSA.V5hjUxkKELA58d1q3HKGBmIqrrzsgtpml3gGEjkYqTKuZrrc; _ga_C4NDLGKVMK=GS1.1.1738066812.8.0.1738066812.60.0.0; smd=4139e5d64bf6dc91d3cd0133af055870-1738067263",
            "priority": "u=0, i",
            "referer": "https://ru.investing.com/news/most-popular-news",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        response = requests.get(newslink, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            article_container = soup.select_one('div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(8) > div > div > div')

            if not article_container:
                return

            if len(article_container.text) > 3000:
                return f'{article_container.text[:3000]}...\n\nЧитать полностью в источнике:\n'
            else:
                return article_container.text
        else:
            logger.warning(
                'Response code = {} on link {}'.format(
                    response.status_code, newslink
                )
            )
    except Exception as e:
        logger.error(
            'Cant retrieve news article  text from {}: {}'.format(
                newslink, e
            )
        )


def get_html_text(newslink) -> str:
    try:
        response = requests.get(newslink)

        if response.status_code == 200:
            tree = html.fromstring(response.content)
            # Используем XPath для извлечения нужного блока
            paragraphs = tree.xpath('//div[@class="article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8"]//p | //div[@class="article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8"]//blockquote')

            # Формируем HTML-код из извлеченных параграфов
            article_html = ''.join(html.tostring(p, encoding='unicode') for p in paragraphs)

            if not article_html:
                return
            return article_html
        else:
            logger.warning(
                'Response code = {} on link {}'.format(
                    response.status_code, newslink
                )
            )
    except Exception as e:
        logger.error(
            'Cant retrieve news article  text from {}: {}'.format(
                newslink, e
            )
        )
