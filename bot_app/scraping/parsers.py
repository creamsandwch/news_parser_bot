

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

from bot_app.parsers import AbstractParser
from bot_app.scraping.driver_context_chrome import selenium_driver


logger = logging.getLogger(__name__)


class InvestingParserSelenium(AbstractParser):
    __name__ = 'investing.com_parser_selenium'
    URL = 'https://ru.investing.com/news/most-popular-news'
    xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/ul/li[1]/article/div/a'

    def __init__(self):
        super().__init__()

    def get_last_news_item_from_url(self, retries=3) -> dict:
        with selenium_driver() as driver:
            for attempt in range(retries):
                try:
                    driver.get(self.URL)
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    news_element = WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, self.xpath))
                    )

                    if news_element:
                        title = news_element.text
                        link = news_element.get_attribute('href')
                        news_id = link.split('-')[-1]

                        if title and link and news_id:
                            logger.debug(f'Found news item - ID: {news_id}, title: {title}, href: {link}')
                            return {
                                'id': news_id,
                                'title': title,
                                'link': link
                            }
                    else:
                        logger.error(f'{self.__name__}: не удалось найти элементы новостей на странице {self.URL}')
                except Exception as e:
                    logger.error(f"Ошибка при парсинге: {e}")
            return None

    @staticmethod
    def get_article_text_selenium(newslink) -> str:
        logger.info('Trying to get article text from {}'.format(newslink))
        with selenium_driver() as driver:
            try:
                driver.get(newslink)
                try:
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    # Ожидание загрузки элемента с текстом статьи
                except TimeoutException:
                    logger.info('Timeout on waiting for body')
                    raise
                try:
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, '#leftColumn > div.WYSIWYG.articlePage')
                        )
                    )
                except TimeoutException:
                    logger.error(
                        'Failed on waiting for #leftColumn > div.WYSIWYG.articlePage'
                    )
                    pass

                # Получение HTML-кода страницы
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                article_container = soup.select_one('#leftColumn > div.WYSIWYG.articlePage')

                if not article_container:
                    logger.warning(
                        'Не найден CSS селектор #leftColumn > div.WYSIWYG.articlePage по ссылке {}'.format(newslink)
                    )
                    article_container = soup.select_one('article')
                    if not article_container:
                        logger.warning('Не найден CSS селектор article')
                        article_container = soup.select_one('div.article-content')
                        if not article_container:
                            logger.error('Вообще никакой CSS селектор не найден')
                            return ""

                # Извлечение текста из всех тегов <p> внутри article_container
                paragraphs = article_container.find_all('p')

                # Инициализация переменных для фильтрации
                start_index = None
                end_index = None

                # Поиск индексов начала и конца
                for index, p in enumerate(paragraphs):
                    text = p.get_text(strip=True)  # Убираем лишние пробелы

                    # Ищем начало (первый параграф после 'Позиция успешно добавлена')
                    if 'Позиция успешно добавлена' in text:
                        start_index = index + 1  # Начинаем со следующего параграфа

                    # Ищем конец (параграф с 'Читайте оригинальную статью на сайте')
                    if 'Читайте оригинальную статью на сайте' in text:
                        end_index = index  # Заканчиваем на текущем параграфе
                        break  # Прерываем цикл, так как конец найден

                # Если начало и конец найдены, извлекаем текст между ними
                if start_index is not None and end_index is not None:
                    article_text = '\n\n'.join(
                        [p.get_text(strip=True) for p in paragraphs[start_index:end_index]]
                    )
                else:
                    # Если начало или конец не найдены, берем все параграфы
                    article_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])

                # Обрезка текста (удаление дефиса в начале, если есть)
                cut_index = article_text[:30].find('-')
                if cut_index != -1:
                    article_text = article_text[cut_index + 1:]

                # Обрезка текста (удаление дефиса в начале, если есть)
                # cut_index = article_text[:30].find('-')
                # if cut_index:
                #     article_text = article_text[cut_index + 1:]

                # Обрезка текста до 2000 символов, если он слишком длинный
                if len(article_container.text) > 2000:
                    return f'{article_text[:2000]}...\n'
                else:
                    return article_text

            except ValueError as e:
                logger.error(
                    'Не удалось получить текст статьи с {}: {}'.format(newslink, e)
                )
