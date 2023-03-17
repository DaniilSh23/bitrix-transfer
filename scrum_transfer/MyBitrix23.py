from pybitrix24 import Bitrix24


class Bitrix23(Bitrix24):
    """
    Наследуюсь от класса Bitrix24 той библиотечки и переопределяю его конструктор.
    В конструкторе нужно сразу прописать значения для _access_token и _refresh_token.

    Как это работает?
        1. Создаём локальное веб-приложение (серверное) на своем портале Битрикс.
        2. От туда берём client_id, client_secret
        3. При создании приложения мы назначили "Путь для первоначальной установки" - это вьюха,
        в которой мы создадим инстанс этого класса.
        4. Битрикс отправит запрос на адрес из пункта выше (3) и в POST запросе прилетят access_token, refresh_token.
        5. В этой вьюхе ("Путь для первоначальной установки") создаём инстанс этого класса со всеми параметрами,
        которые мы уже получили.
    """

    def __init__(self, hostname, client_id, client_secret, access_token, refresh_token):
        super().__init__(hostname, client_id, client_secret)
        self._access_token = access_token
        self._refresh_token = refresh_token
