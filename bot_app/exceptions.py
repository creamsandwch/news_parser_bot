class HTMLBlockNotFound(Exception):
    """Парсер не обнаружил искомый блок на странице."""
    pass


class HTMLError(Exception):
    """Ошибка доступа к странице."""
    pass
