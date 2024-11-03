import time
import signal
import sys

from bot_app.bot import bot
from bot_app.log import logger


ENV_PATH = '.env'
is_running = False


def signal_handler(sig, frame):
    logger.info("Received interrupt signal, stopping polling...")
    sys.exit(0)


def main():
    logger.info("Starting polling...")
    bot.infinity_polling()


if __name__ == '__main__':
    # Set up the signal handler for pressing Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info("Shutting down...")
