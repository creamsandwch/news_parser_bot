import logging
import time
from contextlib import contextmanager

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager


logger = logging.getLogger(__name__)


@contextmanager
def selenium_driver_firefox(retries=1, delay=5) -> webdriver.Firefox:
    """
    Контекстный менеджер для управления драйвером Selenium (Firefox) с поддержкой повторных попыток.

    :param retries: Количество попыток.
    :param delay: Задержка между попытками (в секундах).
    """
    options = FirefoxOptions()
    options.add_argument('--headless')  # Запуск в безголовом режиме (без окна браузера)
    # options.add_argument('--disable-gpu')  # Отключение GPU (может помочь на некоторых системах)
    options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    # options.set_preference('dom.webdriver.enabled', False)  # Отключение флага автоматизации
    # options.set_preference('useAutomationExtension', False)  # Отключение расширений автоматизации

    driver = None
    exc = None
    for attempt in range(retries):
        try:
            # Установка GeckoDriver через webdriver_manager
            service = FirefoxService(
                GeckoDriverManager().install(),
                service_args=['--marionette-port', '2828', '--connect-existing'],
                log_path='geckodriver.log'
            )
            driver = webdriver.Firefox(service=service, options=options)
            driver.implicitly_wait(2)  # Устанавливаем неявное ожидание
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
            if driver:
                driver.quit()  # Закрываем драйвер
