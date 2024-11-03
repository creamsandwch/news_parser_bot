import os
import random
from random_word import RandomWords

from bot_app.parsers import RBCParser


r = RandomWords()
parser = RBCParser()

result = {
    'id': 123,
    'title': r.get_random_word(),
    'link': r.get_random_word()
}


def old_result(self):
    return result


def renew_result(self):
    result['id'] += 1
    return result


parser.get_last_news_item_from_url = old_result.__get__(parser)


print(parser.read_last_news_item_id())

parser.store_last_news_item_id(id=result['id'])
assert str(result['id']) == parser.read_last_news_item_id()

news_to_post = parser.get_last_news_object()
assert news_to_post is None


parser.get_last_news_item_from_url = renew_result.__get__(parser)
news_to_post = parser.get_last_news_object()
assert news_to_post is not None
print(news_to_post)
