import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


# Настройка логирования
logger = logging.getLogger(__name__)


def get_article_text_selenium(newslink) -> str:
    options = Options()
    options.add_argument('--headless')  # Запустите браузер в фоновом режиме
    options.add_argument(
            (
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        )
    options.add_argument('--headless')  # Запуск в фоновом режиме
    options.add_argument(
        '--disable-blink-features=AutomationControlled'
    )  # Отключение автоматизации
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install())
    )
    driver.implicitly_wait(2)  # Устанавливаем неявное ожидание

    try:
        driver.get(newslink)

        # Ожидание загрузки элемента с текстом статьи
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(8) > div > div > div'
                )
            )
        )

        # Получение HTML-кода страницы
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
        driver.quit()  # Закрыть драйвер после завершения работы
