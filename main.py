from bot_app.bot import bot


if __name__ == '__main__':
    try:
        bot.polling()
    except Exception as e:
        print(e)
