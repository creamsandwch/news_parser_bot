import logging
from contextlib import contextmanager
import time

from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.webdriver import WebDriver as EdgeWebDriver
from selenium.common.exceptions import TimeoutException, WebDriverException


from bot_app.drivers import DRIVERS


logger = logging.getLogger(__name__)


@contextmanager
def selenium_driver(retries=3, delay=60) -> webdriver.Edge:
    """
    Контекстный менеджер для управления драйвером Selenium (Edge) с поддержкой повторных попыток.

    :param retries: Количество попыток.
    :param delay: Задержка между попытками (в секундах).
    """
    options = EdgeOptions()
    # options.add_argument('--headless')  # Запуск в безголовом режиме (без окна браузера)
    # options.add_argument('--disable-gpu')  # Отключение GPU
    # options.add_argument('--disable-dev-shm-usage')  # Отключение использования /dev/shm
    # options.add_argument('--no-sandbox')  # Отключение песочницы
    # options.add_argument('--disable-blink-features=AutomationControlled')  # Отключение автоматизации
    # options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')  # Изменение user-agent

    driver = None
    exc = None
    for attempt in range(retries):
        try:
            # Установка EdgeDriver через webdriver_manager
            service = EdgeService(executable_path=DRIVERS.get('msedgedriver'), options=options)
            driver = EdgeWebDriver(service=service, options=options)

            driver.implicitly_wait(60)  # Увеличено время неявного ожидания
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
                driver.quit()  # Закрываем драйвер
