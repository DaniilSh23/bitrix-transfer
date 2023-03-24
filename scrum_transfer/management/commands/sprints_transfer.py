from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Sprint


class Command(BaseCommand):
    """
    Команда для трансфера спринтов из облака в коробку
    """
    def handle(self, *args, **options):
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

        scrum_objects = Scrums.objects.all()
        for i_numb, i_scrum in enumerate(scrum_objects):  # итерируемся по скрамам
            logger.info(f'Скрам № {i_numb + 1}')

            if i_scrum.is_archived:
                logger.info(f'Скрам: {i_scrum.scrum_title} в архиве. Пропускаем его...')
                continue

            # Получаем список спринтов из облака
            logger.info(f'Запрашиваем список спринтов из облака для скрама: {i_scrum.scrum_title}')
            method = 'tasks.api.scrum.sprint.list'
            params = {
                'filter': {
                    'GROUP_ID': i_scrum.scrum_cloud_id,
                },
            }
            sprints_lst = bitra_cloud.call(method=method, params=params)
            if not sprints_lst.get('result'):  # Если список спринтов не получен
                logger.warning(f'Запрос на получение из ОБЛАКА спринтов для скрама {i_scrum.scrum_title} НЕ УДАЛСЯ.\n\n'
                               f'Запрос {method} с параметрами {params}, ответ:\n{sprints_lst}')
                raise CommandError

            sprints_lst = sprints_lst.get('result')
            for j_numb, j_sprint in enumerate(sprints_lst):  # итерируемся по списку спринтов
                logger.info(f'Спринт № {j_numb + 1}')

                # Проверка, что спринт ранее был создан
                check_sprint = Sprint.objects.filter(sprint_id_cloud=j_sprint.get('id'))
                if len(check_sprint) > 0:
                    logger.info(f"Спринт ранее уже был создан. Пропускаем его...")
                    continue

                # Создаём спринт в коробке
                logger.info(f'Запрос на создания спринта в КОРОБКЕ для скрама {i_scrum.scrum_title}')
                method = 'tasks.api.scrum.sprint.add'
                params = {
                    'fields': {
                        'groupId': i_scrum.scrum_box_id,
                        'name': j_sprint.get('name'),
                        'dateStart': j_sprint.get('dateStart'),
                        'dateEnd': j_sprint.get('dateEnd'),
                        'status': j_sprint.get('status'),
                        'createdBy': Settings.objects.get(key='worker_in_box_id').value,
                        'sort': j_sprint.get('sort'),
                    },
                }
                create_sprint = bitra_box.call(method=method, params=params)
                if not create_sprint.get('result'):
                    logger.warning(f'Запрос на создание спринта в скраме {i_scrum.scrum_title} НЕ УДАЛСЯ.\n\n'
                                   f'Запрос: {method}|{params}\nОтвет: {create_sprint}')
                    raise CommandError

                # Записываем данные о спринте в БД
                sprint_obj = Sprint.objects.update_or_create(
                    sprint_id_cloud=j_sprint.get('id'),
                    defaults={
                        'sprint_id_cloud': j_sprint.get('id'),
                        'sprint_id_box': create_sprint.get('result').get('id'),
                        'scrum_cloud_id': i_scrum.scrum_cloud_id,
                        'scrum_box_id': i_scrum.scrum_box_id,
                        'sprint_name': j_sprint.get('name'),
                    }
                )
                logger.success(f'Спринт {j_sprint.get("name")} для скрама {i_scrum.scrum_title} '
                               f'{"создан" if sprint_obj[1] else "обновлён"} в БД.')
