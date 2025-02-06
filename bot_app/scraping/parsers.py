from bot_app.parsers import AbstractParser


from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import logging
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


class InvestingParserSelenium(AbstractParser):
    __name__ = 'investing.com_parser_selenium'
    URL = 'https://ru.investing.com/news/most-popular-news'
    xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div/div/ul/li[1]/article/div/a'

    def __init__(self):
        # Настройка Selenium
        super().__init__()
        self.options = Options()
        self.options.add_argument(
            (
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        )
        self.options.add_argument('--headless')  # Запуск в фоновом режиме
        self.options.add_argument(
            '--disable-blink-features=AutomationControlled'
        )  # Отключение автоматизации
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=self.options
        )

    def get_last_news_item_from_url(self) -> dict:
        try:
            self.driver.get(self.URL)
            # Ожидание загрузки страницы и появления элементов новостей
            news_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, self.xpath))
            )

            if news_element:
                # Извлекаем данные
                title = news_element.text
                link = news_element.get_attribute('href')
                news_id = link.split('-')[-1]  # Извлекаем ID из ссылки (например, 2645572)

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
            logger.error(f'Ошибка при парсинге: {e}')
        finally:
            self.driver.quit()  # Закрываем браузер после завершения

        return None

    def get_article_text_selenium(self, newslink) -> str:
        self.driver.implicitly_wait(2)  # Устанавливаем неявное ожидание

        try:
            self.driver.get(newslink)

            # Ожидание загрузки элемента с текстом статьи
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(8) > div > div > div'
                    )
                )
            )

            # Получение HTML-кода страницы
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            article_container = soup.select_one('div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(8) > div > div > div')

            if not article_container:
                return ""

            paragraphs = article_container.find_all('p')
            article_text = '\n\n'.join([p.get_text() for p in paragraphs])

            if len(article_container.text) > 2000:
                return f'{article_text[:2000]}...\n'
            else:
                return article_text

        except Exception as e:
            logger.error(
                'Не удалось получить текст статьи с {}: {}'.format(newslink, e)
            )
        finally:
            self.driver.quit()  # Закрыть драйвер после завершения работы
