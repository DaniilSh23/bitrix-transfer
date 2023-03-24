from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Epic


class Command(BaseCommand):
    """
    Команда для трансфера эпиков из облака в коробку.
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

        scrums = Scrums.objects.all()
        for i_numb, i_scrum in enumerate(scrums):
            logger.info(f'Скрам № {i_numb + 1} | {i_scrum.scrum_title}')

            if i_scrum.is_archived:
                logger.info(f'Скрам: {i_scrum.scrum_title} в архиве. Пропускаем его...')
                continue

            # Получаем список эпиков из облака
            logger.info(f'Получаем список эпиков из облака.')
            method = 'tasks.api.scrum.epic.list'
            params = {
                'filter': {
                    'GROUP_ID': i_scrum.scrum_cloud_id,
                },
            }
            epics_lst = bitra_cloud.call(method=method, params=params)
            if epics_lst.get('result') is None:
                logger.warning(f'Неудачный запрос для получения списка эпиков из облака! '
                               f'Запрос: {method}|{params}\nОтвет:{epics_lst}')
                raise CommandError

            for j_numb, j_epic in enumerate(epics_lst.get('result')):
                logger.info(f'\t\tЭпик № {j_numb + 1} | Скрам: {i_scrum.scrum_title}')

                # Проверка, что эпик ранее был создан
                check_epic = Epic.objects.filter(epic_id_cloud=j_epic.get('id'))
                if len(check_epic) > 0:
                    logger.info(f"Эпик ранее уже был создан в коробке. Пропускаем его...")
                    continue

                # Создаём эпик в коробке
                logger.info(f'\t\tСоздаём эпик в коробке')
                method = 'tasks.api.scrum.epic.add'
                params = {
                    'fields': {
                        'groupId': i_scrum.scrum_box_id,
                        'name': j_epic.get('name'),
                        'description': j_epic.get('description'),
                        'createdBy': Settings.objects.get(key='worker_in_box_id').value,
                        'color': j_epic.get('color'),
                    },
                }
                create_epic_in_box = bitra_box.call(method=method, params=params)
                if not create_epic_in_box.get('result'):
                    logger.warning(f'\t\tНеудачный запрос для создания эпика в коробке.\n\n'
                                   f'\t\tЗапрос: {method}|{params}\n\t\tОтвет: {create_epic_in_box}')
                    raise CommandError

                # Записываем данные об эпике в БД
                Epic.objects.update_or_create(
                    epic_id_cloud=j_epic.get('id'),
                    defaults={
                        'epic_id_cloud': j_epic.get('id'),
                        'epic_id_box': create_epic_in_box.get('result').get('id'),
                        'scrum_cloud_id': i_scrum.scrum_cloud_id,
                        'scrum_box_id': i_scrum.scrum_box_id,
                        'epic_name': j_epic.get('name'),
                        'epic_files': j_epic.get('files'),
                    }
                )
                logger.success(f'\t\tУспешно создан эпик: {j_epic.get("name")}|Скрам: {i_scrum.scrum_title}')
