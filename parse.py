import json

from bs4 import BeautifulSoup


with open('data.json', encoding='utf-8') as file:
    html_text = file.read()


json_data = json.loads(html_text)

from bot_app.utils import find_key_path


print(find_key_path(json_data, '_newsList'))

soup = BeautifulSoup(html_text, 'html.parser')
