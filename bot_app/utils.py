import json

from bs4 import BeautifulSoup


def find_key(data, key):
    """Для поиска данных по ключу во вложенных словарях."""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            result = find_key(value, key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_key(item, key)
            if result is not None:
                return result
    return None


def find_key_path(data, key, path=None):
    """Возвращает путь из ключей до нужного ключа во вложенных словарях."""
    if path is None:
        path = []

    if isinstance(data, dict):
        if key in data:
            return path + [key]
        for k, value in data.items():
            result = find_key_path(value, key, path + [k])
            if result is not None:
                return result
    elif isinstance(data, list):
        for index, item in enumerate(data):
            result = find_key_path(item, key, path + [index])
            if result is not None:
                return result
    return None

# пример
# with open('cache', 'r', encoding='utf-8') as file:
#     html_content = file.read()


# # Создаем объект BeautifulSoup
# soup = BeautifulSoup(html_content, 'html.parser')

# # Находим тег <script> с нужным id
# script_tag = soup.find('script', id='__NEXT_DATA__')
# json_data = json.loads(script_tag.string)

# target_value = "_breakingNewsList"
# path = find_key_path(json_data, target_value)

# if path is not None:
#     print(f"Путь к объекту: {path}")
# else:
#     print("Объект не найден.")
