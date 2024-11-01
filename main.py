from bot_app.bot import bot


ENV_PATH = '.env'


def main():
    bot.polling()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
