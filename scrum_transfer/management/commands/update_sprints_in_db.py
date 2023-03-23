from django.core.management import BaseCommand
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Scrums, Settings, Sprint


class Command(BaseCommand):
    """
    Команда для обновления записей о спринтах в БД.
    (Родилась, когда я понял, что вместо ID спринта коробки поставил название)
    """
    def handle(self, *args, **options):
        self.stdout.write('Старт обновления записей о спринтах!')

        # Создаём инстанс битры ОБЛАКО
        bitra_cloud = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_cloud").value,
            client_id=Settings.objects.get(key="client_id_cloud").value,
            client_secret=Settings.objects.get(key="client_secret_cloud").value,
            access_token=Settings.objects.get(key="access_token_cloud").value,
            refresh_token=Settings.objects.get(key="refresh_token_cloud").value,
        )
        # bitra_cloud.refresh_tokens()

        # Создаём инстанс битры КОРОБКА
        bitra_box = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_box").value,
            client_id=Settings.objects.get(key="client_id_box").value,
            client_secret=Settings.objects.get(key="client_secret_box").value,
            access_token=Settings.objects.get(key="access_token_box").value,
            refresh_token=Settings.objects.get(key="refresh_token_box").value,
        )
        # bitra_box.refresh_tokens()

        all_scrums = Scrums.objects.all()
        for i_scrum in all_scrums:

            # Получаем список спринтов
            method = 'tasks.api.scrum.sprint.list'
            params = {
                'filter': {
                    'GROUP_ID': i_scrum.scrum_box_id,
                },
            }
            sprint_lst = bitra_box.call(method=method, params=params)
            if not sprint_lst.get('result'):     # Если список спринтов не получен
                logger.warning(f'Запрос на получение спринтов для скрама {i_scrum.scrum_title} НЕ УДАЛСЯ.\n\n'
                               f'Запрос {method} с параметрами {params}, ответ:\n{sprint_lst}')
                input('нажми чё угодно, если пропустить скрам и продолжить или CTRL+C чтобы остановить комманду.')
            sprint_lst = sprint_lst.get('result')

            for j_numb, j_sprint in enumerate(sprint_lst):    # итерируемся по списку спринтов
                logger.info(f'Спринт № {j_numb + 1}')
                try:
                    sprint_from_db = Sprint.objects.get(scrum_box_id=i_scrum.scrum_box_id, sprint_name=j_sprint.get("name"))
                except Exception as error:
                    logger.warning(f'Ошибочка, когда спринт обновить хотим. Текст: {error}. '
                                   f'Берём в БД по таким ключам: scrum_box_id={i_scrum.scrum_box_id} | '
                                   f'sprint_name={j_sprint.get("name")}. Ну а из запроса имеем вот это: {j_sprint}')
                    input('Что делать будем? Дальше или CTRL+C')
                    continue
                sprint_from_db.sprint_id_box = j_sprint.get('id')
                sprint_from_db.save()
                logger.success(f'Спринт: {sprint_from_db.sprint_name!r} | скрам: {i_scrum.scrum_title!r}')
                # input(Sprint.objects.get(sprint_id_box=j_sprint.get('id')).sprint_id_box)