from bot_app.scraping.parsers import InvestingParserSelenium

parser = InvestingParserSelenium()


newslink = 'https://ru.investing.com/news/world-news/article-2670738'

try:
    raw_text = parser.get_article_text_selenium(newslink)
    if raw_text is None:
        raise Exception('Текст не получен')
    if raw_text:
        print('Success')
        print('got text: {}'.format(raw_text[:30]))
except Exception as e:
    print(e)
