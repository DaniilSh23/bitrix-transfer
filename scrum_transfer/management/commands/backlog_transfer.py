from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Backlog


class Command(BaseCommand):
    """
    Команда для трансфера бэклогов.
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

        # Получаем объекты скрамов из БД
        scrum_objects = Scrums.objects.all()

        for i_numb, i_scrum in enumerate(scrum_objects):  # Берём каждый скрам
            logger.info(f'Обрабатываем скрам № {i_numb + 1} | {i_scrum.scrum_title}')

            if i_scrum.is_archived:
                logger.info(f'Скрам: {i_scrum.scrum_title} в архиве. Пропускаем его...')
                continue

            # Проверка, что бэклог уже есть в БД
            check_backlog = Backlog.objects.filter(scrum_box_id=i_scrum.scrum_box_id)
            if len(check_backlog) > 0:
                logger.info(f"Бэклог ранее был создан. Пропускаем его...")
                continue

            # получаем бэклог скрама из облака
            method = 'tasks.api.scrum.backlog.get'
            params = {
                'id': i_scrum.scrum_cloud_id,
            }
            i_backlog_cloud = bitra_cloud.call(method=method, params=params)
            if not i_backlog_cloud.get('result'):  # проверка, что запрос НЕ был успешным
                logger.error(f'НЕ УДАЛСЯ запрос бэклога из ОБЛАКА для скрама: {i_scrum.scrum_title}.\n'
                             f'Запрос: {method} | {params}:\nОтвет: {i_backlog_cloud}')
                raise CommandError

            # Создаём бэклог в коробке
            method = 'tasks.api.scrum.backlog.add'
            params = {
                'fields': {
                    'groupId': i_scrum.scrum_box_id,  # ID скрама
                    'createdBy': Settings.objects.get(key='worker_in_box_id').value,  # ID создателя
                },
            }
            i_backlog_box = bitra_box.call(method=method, params=params)
            if not i_backlog_box.get('result'):  # проверка, что запрос НЕ был успешным
                logger.warning(f'НЕ УДАЛСЯ запрос для создания бэклога в коробке для скрама: {i_scrum.scrum_title}.\n'
                               f'Запрос: {method} | {params}:\nОтвет: {i_backlog_cloud}\n'
                               f'Если он создан, то будет выполнен запрос его из коробки.')

                if i_backlog_box.get('error_description') == 'Backlog already added':  # если бэклог уже есть
                    logger.info(f'Бэклог уже есть! '
                                f'Запрос на получение бэклога из КОРОБКИ для скрама: {i_scrum.scrum_title}')

                    # Получаем бэклог скрама из коробки
                    method = 'tasks.api.scrum.backlog.get'
                    params = {
                        'id': i_scrum.scrum_box_id,
                    }
                    get_i_backlog_from_box = bitra_box.call(method=method, params=params)
                    if get_i_backlog_from_box.get('result'):
                        i_backlog_box = get_i_backlog_from_box
                    else:
                        logger.error(f'НЕ УДАЛСЯ запрос для получения бэклога '
                                     f'из КОРОБКИ для скрама: {i_scrum.scrum_title}.\n'
                                     f'Запрос: {method} | {params}:\nОтвет: {i_backlog_cloud}')
                        raise CommandError
                else:
                    logger.error(f'Нет, все таки бэклог не получен и не сохранен в БД.')
                    raise CommandError

            # Запись данных о бэклоге в БД проекта
            backlog_wrt_rslt = Backlog.objects.update_or_create(
                backlog_id_cloud=i_backlog_cloud.get('result').get('id'),
                defaults={
                    'backlog_id_cloud': i_backlog_cloud.get('result').get('id'),
                    'backlog_id_box': i_backlog_box.get('result').get('id'),
                    'scrum_cloud_id': i_scrum.scrum_cloud_id,
                    'scrum_box_id': i_scrum.scrum_box_id,
                }
            )
            logger.success(f'Бэклог скрама: {i_scrum.scrum_title} {"создан" if backlog_wrt_rslt[1] else "обновлён"}')