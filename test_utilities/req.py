import requests


resp = requests.get('https://ru.investing.com/news/latest-news')
with open('resp_cache', 'w', encoding='utf-8') as file:
    file.write(resp.text)
