import logging
import time
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from selenium_stealth import stealth


logger = logging.getLogger(__name__)
caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}


@contextmanager
def selenium_driver(retries=1, delay=5) -> webdriver.Chrome:
    """
    Контекстный менеджер для управления драйвером Selenium с поддержкой повторных попыток.

    :param retries: Количество попыток.
    :param delay: Задержка между попытками (в секундах).
    """
    options = ChromeOptions()
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--ignore-ssl-errors')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--enable-unsafe-swiftshader')
    # options.add_argument('--disable-webgl')
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    # options.add_argument('--ignore-certificate-errors-spki-list')
    # options.add_argument('--disable-blink-features=AutomationControlled')

    # stealth
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    exc = None
    for attempt in range(retries):
        try:
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(2)  # Устанавливаем неявное ожидание
            stealth(
                driver,
                languages=["ru-RU", "RU"],
                vendor="Google Inc.",
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            yield driver  # Возвращаем драйвер
            break  # Успешное выполнение, выходим из цикла
        except (TimeoutException, WebDriverException) as e:
            exc = e
            logger.warning(f"Попытка {attempt + 1} из {retries} не удалась: {e}")
            if attempt == retries - 1:  # Если это последняя попытка
                logger.error(f"Все попытки завершились ошибкой: {e}")
                raise
            time.sleep(delay)  # Ждем перед следующей попыткой
        finally:
            if driver is not None and (
                attempt == retries - 1 or not isinstance(
                    exc, (TimeoutException, WebDriverException)
                )
            ):
                driver.close()  # Закрываем драйвер
