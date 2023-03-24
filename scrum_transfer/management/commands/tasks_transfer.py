import time

from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Backlog, BitrixUsers, Sprint, ScrumTask, Epic


class Command(BaseCommand):
    """
    Команда для создания задач в скрамах
    """

    def handle(self, *args, **options):
        self.stdout.write('Начинаем создание задач в скрамах.')

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
        for i_numb, i_scrum in enumerate(scrum_objects):
            logger.info(f'Скрам №{i_numb + 1}|{i_scrum.scrum_title}')

            if i_scrum.is_archived:
                logger.info(f'Скрам: {i_scrum.scrum_title} в архиве. Пропускаем его...')
                continue

            start_step = None
            while True:
                # Запрашиваем задачи скрама из облака
                method = 'tasks.task.list'
                params = {
                    'filter': {
                        'GROUP_ID': i_scrum.scrum_cloud_id,  # ID группы(скрама)
                    },
                    'start': start_step,  # Выводить задачи, начиная с ...(параметр next в ответе)
                }
                i_cloud_tasks = bitra_cloud.call(method=method, params=params)
                if not i_cloud_tasks.get('result'):  # Проверка, что данные получены
                    logger.error(f'\tНЕ удалось получить данные О ЗАДАЧАХ по скраму {i_scrum.scrum_title!r}. '
                                 f'Дальнейшее выполнение команды не имеет смысла.'
                                 f'Будет выполнена остановка выполнения команды.\n'
                                 f'Запрос: {method}|{params}\nОтвет: {i_cloud_tasks}')
                    raise CommandError

                for j_cloud_task in i_cloud_tasks.get('result').get('tasks'):

                    # Проверка: если задача уже есть в БД, то не создаём её в коробке
                    task_in_db_lst = ScrumTask.objects.filter(task_id_cloud=j_cloud_task.get('id'))
                    if len(task_in_db_lst) > 0:
                        logger.info(f'Задача {j_cloud_task.get("title")!r} УЖЕ ЕСТЬ В БД и НЕ будет создана в коробке!')
                        continue

                    # Запрашиваем инфу о задаче в ключе скрама
                    method = 'tasks.api.scrum.task.get'
                    params = {'id': j_cloud_task.get('id')}
                    j_cloud_scrum_task = bitra_cloud.call(method=method, params=params)
                    if not j_cloud_scrum_task.get('result'):  # Проверка, что данные получены
                        logger.error(f'\tНе удалось получить данные О ЗАДАЧАХ В КЛЮЧЕ СКРАМА '
                                     f'для скрама: {i_scrum.scrum_title!r}. '
                                     f'Дальнейшее выполнение команды не имеет смысла.'
                                     f'Будет выполнена остановка выполнения команды.\n'
                                     f'Запрос: {method}|{params}\nОтвет: {j_cloud_scrum_task}')
                        raise CommandError

                    # Получаем нужные коробочные параметры для создания задачи
                    created_by = j_cloud_task.get('createdBy')  # Создатель задачи
                    if created_by:
                        try:
                            created_by = BitrixUsers.objects.get(user_id_cloud=created_by).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                           f'Параметр для создания задачи == CREATED_BY | '
                                           f'Облачный ID юзера == {j_cloud_task.get("createdBy")}'
                                           f'\nТекст ошибки: {error}')
                            # raise CommandError
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': created_by,    # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}.'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            created_by = user_db_write_rslt[0].user_id_box

                    scrum_task_created_by = j_cloud_scrum_task.get('result').get('createdBy')  # Создатель задачи(скрам)

                    if scrum_task_created_by:
                        try:
                            scrum_task_created_by = BitrixUsers.objects.get(user_id_cloud=scrum_task_created_by).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для ОБНОВЛЕНИЯ СКРАМ задачи в коробке.'
                                           f'Параметр для создания задачи == createdBy | '
                                           f'Облачный ID юзера == {j_cloud_scrum_task.get("result").get("createdBy")}'
                                           f'\nТекст ошибки: {error}')
                            # raise CommandError
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': scrum_task_created_by,    # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            scrum_task_created_by = user_db_write_rslt[0].user_id_box

                    scrum_task_modified_by = j_cloud_scrum_task.get('result').get(
                        'modifiedBy')  # Кто модифицировал задачу(скрам)
                    if scrum_task_modified_by:
                        try:
                            scrum_task_modified_by = BitrixUsers.objects.get(user_id_cloud=scrum_task_modified_by).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для ОБНОВЛЕНИЯ СКРАМ задачи в коробке.'
                                           f'Параметр для создания задачи == createdBy | '
                                           f'Облачный ID юзера == {j_cloud_scrum_task.get("result").get("modifiedBy")}'
                                           f'\nТекст ошибки: {error}')
                            # raise CommandError
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': scrum_task_modified_by,    # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            scrum_task_modified_by = user_db_write_rslt[0].user_id_box

                    responsible_id = j_cloud_task.get('responsibleId')  # Ответственный
                    if responsible_id:
                        try:
                            responsible_id = BitrixUsers.objects.get(user_id_cloud=responsible_id).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                           f'Параметр для создания задачи == RESPONSIBLE_ID | '
                                           f'Облачный ID юзера == {j_cloud_task.get("responsibleId")}'
                                           f'\nТекст ошибки: {error}\n')
                            # continue
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': responsible_id,    # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            responsible_id = user_db_write_rslt[0].user_id_box

                    cloud_accomplices_lst = j_cloud_task.get('accomplices')  # Соисполнители (список)
                    if len(cloud_accomplices_lst) > 0:  # Если список не пустой
                        box_accomplices_lst = []
                        for i_cloud_usr_id in cloud_accomplices_lst:
                            try:
                                accomplices_id = BitrixUsers.objects.get(user_id_cloud=i_cloud_usr_id).user_id_box
                                box_accomplices_lst.append(accomplices_id)
                            except Exception as error:
                                logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                               f'Параметр для создания задачи == ACCOMPLICES (не найден 1 из списка) | '
                                               f'Облачный ID юзера == {i_cloud_usr_id}.'
                                               f'\nТекст ошибки: {error}')

                                logger.warning(f'Ошибка при получении юзера из БД: {error}')
                                # Получаем детальную инфу о пользователе
                                method = 'user.get'
                                params = {
                                    'ID': i_cloud_usr_id,  # ID пользователя в битре
                                    # 'EMAIL': 'd.shestakov@cfunalog.ru'
                                }
                                user_which_not_found = bitra_cloud.call(method=method, params=params)

                                # Запрашиваем детальную инфу о юзере в коробке
                                method = 'user.get'
                                params = {
                                    'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                                }
                                user_detail_from_box = bitra_box.call(method=method, params=params)
                                if not user_detail_from_box.get('result'):
                                    logger.error(
                                        f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                        f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                        f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                        f'Пропускаем юзера...')
                                    continue

                                # Обновляем или создаём запись о юзере в БД
                                user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                    email=user_which_not_found.get('result')[0].get('EMAIL'),
                                    defaults={
                                        "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                        "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                        "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                        "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                                f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                    }
                                )
                                logger.success(
                                    f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                    f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                                box_accomplices_lst.append(user_db_write_rslt[0].user_id_box)

                    else:  # Иначе, когда список пустой
                        box_accomplices_lst = []

                    cloud_auditors_lst = j_cloud_task.get('accomplices')  # Наблюдатели (список)
                    if len(cloud_auditors_lst) > 0:  # Если список не пустой
                        box_auditors_lst = []
                        for i_cloud_usr_id in cloud_auditors_lst:
                            try:
                                auditor_id = BitrixUsers.objects.get(user_id_cloud=i_cloud_usr_id).user_id_box
                                box_auditors_lst.append(auditor_id)
                            except Exception as error:
                                logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                               f'Параметр для создания задачи == AUDITORS (не найден 1 из списка) | '
                                               f'Облачный ID юзера == {i_cloud_usr_id}'
                                               f'\nТекст ошибки: {error}')

                                logger.warning(f'Ошибка при получении юзера из БД: {error}')
                                # Получаем детальную инфу о пользователе
                                method = 'user.get'
                                params = {
                                    'ID': i_cloud_usr_id,  # ID пользователя в битре
                                    # 'EMAIL': 'd.shestakov@cfunalog.ru'
                                }
                                user_which_not_found = bitra_cloud.call(method=method, params=params)

                                # Запрашиваем детальную инфу о юзере в коробке
                                method = 'user.get'
                                params = {
                                    'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                                }
                                user_detail_from_box = bitra_box.call(method=method, params=params)
                                if not user_detail_from_box.get('result'):
                                    logger.error(
                                        f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                        f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                        f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                        f'Пропускаем юзера...')
                                    continue

                                # Обновляем или создаём запись о юзере в БД
                                user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                    email=user_which_not_found.get('result')[0].get('EMAIL'),
                                    defaults={
                                        "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                        "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                        "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                        "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                                f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                    }
                                )
                                logger.success(
                                    f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                    f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                                box_auditors_lst.append(user_db_write_rslt[0].user_id_box)

                    else:  # Иначе, когда список пустой
                        box_auditors_lst = []

                    changed_by = j_cloud_task.get('changedBy')  # Кто изменил задачу
                    if changed_by:
                        try:
                            changed_by = BitrixUsers.objects.get(user_id_cloud=changed_by).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                           f'Параметр для создания задачи == CHANGED_BY | '
                                           f'Облачный ID юзера == {j_cloud_task.get("changed_by")}'
                                           f'\nТекст ошибки: {error}')
                            # raise CommandError
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': changed_by,  # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            changed_by = user_db_write_rslt[0].user_id_box

                    status_changed_by = j_cloud_task.get('statusChangedBy')  # Кто изменил статус задачи
                    if status_changed_by:
                        try:
                            status_changed_by = BitrixUsers.objects.get(user_id_cloud=status_changed_by).user_id_box
                        except Exception as error:
                            logger.warning(f'\t\tНе найден коробочный ID юзера для создания задачи в коробке.'
                                           f'Параметр для создания задачи == STATUS_CHANGED_BY | '
                                           f'Облачный ID юзера == {j_cloud_task.get("statusChangedBy")}'
                                           f'\nТекст ошибки: {error}')
                            # raise CommandError
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': status_changed_by,  # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            method = 'user.get'
                            params = {
                                'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                            }
                            user_detail_from_box = bitra_box.call(method=method, params=params)
                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue

                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            status_changed_by = user_db_write_rslt[0].user_id_box

                    closed_by = j_cloud_task.get('closedBy')  # Кто закрыл задачу
                    if closed_by and str(closed_by) != '0':
                        try:
                            closed_by = BitrixUsers.objects.get(user_id_cloud=closed_by).user_id_box
                        except Exception as error:
                            # continue
                            logger.warning(f'Ошибка при получении юзера из БД: {error}')
                            # Получаем детальную инфу о пользователе
                            method = 'user.get'
                            params = {
                                'ID': closed_by,  # ID пользователя в битре
                                # 'EMAIL': 'd.shestakov@cfunalog.ru'
                            }
                            user_which_not_found = bitra_cloud.call(method=method, params=params)

                            # Запрашиваем детальную инфу о юзере в коробке
                            try:
                                method = 'user.get'
                                params = {
                                    'EMAIL': user_which_not_found.get('result')[0].get('EMAIL')
                                }
                            except IndexError as error:
                                logger.error(f'{error} | user_which_not_found == {user_which_not_found} | {closed_by}')
                            user_detail_from_box = bitra_box.call(method=method, params=params)

                            if not user_detail_from_box.get('result'):
                                logger.error(
                                    f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: '
                                    f'{user_which_not_found.get("result")[0].get("EMAIL")}.\n'
                                    f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}'
                                    f'Пропускаем задачу...')
                                continue
                            # Обновляем или создаём запись о юзере в БД
                            user_db_write_rslt = BitrixUsers.objects.update_or_create(
                                email=user_which_not_found.get('result')[0].get('EMAIL'),
                                defaults={
                                    "user_id_cloud": user_which_not_found.get('result')[0].get('ID'),
                                    "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                                    "email": user_which_not_found.get('result')[0].get('EMAIL'),
                                    "name": f"{user_which_not_found.get('result')[0].get('NAME')} "
                                            f"{user_which_not_found.get('result')[0].get('LAST_NAME')}",
                                }
                            )
                            logger.success(
                                f"Пользователь {user_which_not_found.get('result')[0].get('EMAIL')} "
                                f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")
                            closed_by = user_db_write_rslt[0].user_id_box

                    # Создаём задачу в коробке
                    method = 'tasks.task.add'
                    params = {
                        'fields': {
                            'TITLE': j_cloud_task.get('title'),
                            'DESCRIPTION': j_cloud_task.get('description'), 'MARK': j_cloud_task.get('mark'),
                            'PRIORITY': j_cloud_task.get('priority'),
                            'STATUS': j_cloud_task.get('status'), 'MULTITASK': j_cloud_task.get('multitask'),
                            'NOT_VIEWED': j_cloud_task.get('notViewed'), 'REPLICATE': j_cloud_task.get('replicate'),
                            'GROUP_ID': i_scrum.scrum_box_id, 'STAGE_ID': None,
                            'CREATED_BY': created_by, 'CREATED_DATE': j_cloud_task.get('createdDate'),
                            'RESPONSIBLE_ID': responsible_id, 'ACCOMPLICES': box_accomplices_lst,
                            'AUDITORS': box_auditors_lst, 'CHANGED_BY': changed_by,
                            'STATUS_CHANGED_BY': status_changed_by, 'CHANGED_DATE': j_cloud_task.get('changedDate'),
                            'STATUS_CHANGED_DATE': j_cloud_task.get('statusChangedDate'), 'CLOSED_BY': closed_by,
                            'CLOSED_DATE': j_cloud_task.get('closedDate'),
                            'ACTIVITY_DATE': j_cloud_task.get('activityDate'),
                            'DATE_START': j_cloud_task.get('dateStart'), 'DEADLINE': j_cloud_task.get('deadline'),
                            'ALLOW_CHANGE_DEADLINE': j_cloud_task.get('allowChangeDeadline'),
                            'ALLOW_TIME_TRACKING': j_cloud_task.get('allowTimeTracking'),
                            'TASK_CONTROL': j_cloud_task.get('taskControl'),
                            'ADD_IN_REPORT': j_cloud_task.get('addInReport'),
                            'START_DATE_PLAN': j_cloud_task.get('startDatePlan'),
                            'END_DATE_PLAN': j_cloud_task.get('endDatePlan'),
                            'TIME_ESTIMATE': j_cloud_task.get('timeEstimate'),
                            'TIME_SPENT_IN_LOGS': j_cloud_task.get('timeSpentInLogs'),
                            'MATCH_WORK_TIME': j_cloud_task.get('matchWorkTime'),
                            # 'FORUM_TOPIC_ID': 0, 'FORUM_ID': 0, 'SITE_ID': 0,
                            'SUBORDINATE': j_cloud_task.get('subordinate'), 'FAVORITE': j_cloud_task.get('favorite'),
                            'EXCHANGE_MODIFIED': j_cloud_task.get('exchangeModified'),
                            'EXCHANGE_ID': j_cloud_task.get('exchangeId'),
                            'OUTLOOK_VERSION': j_cloud_task.get('outlookVersion'),
                            'VIEWED_DATE': j_cloud_task.get('viewedDate'), 'SORTING': j_cloud_task.get('sorting'),
                            'DURATION_PLAN': j_cloud_task.get('durationPlan'),
                            'DURATION_FACT': j_cloud_task.get('durationFact'),
                            'DURATION_TYPE': j_cloud_task.get('durationType'),
                            'IS_MUTED': j_cloud_task.get('isMuted'), 'IS_PINNED': j_cloud_task.get('isPinned'),
                            'IS_PINNED_IN_GROUP': j_cloud_task.get('isPinnedInGroup'),
                            'CHECKLIST': j_cloud_task.get('checklist'), 'UF_CRM_TASK': j_cloud_task.get('ufCrmTask'),
                            'UF_MAIL_MESSAGE': j_cloud_task.get('ufMailMessage'),
                        }
                    }
                    j_box_task = bitra_box.call(method=method, params=params)  # Создание задачи в коробке
                    if not j_box_task.get('result'):  # Проверка, что данные получены
                        logger.error(f'\t\tНе удалось СОЗДАТЬ ЗАДАЧУ В КОРОБКЕ! '
                                     f'Название задачи: {j_cloud_task.get("title")}'
                                     f'Задача из скрама: {i_scrum.scrum_title!r}. '
                                     f'Дальнейшее выполнение команды не имеет смысла.'
                                     f'Будет выполнена остановка выполнения команды.\n'
                                     f'Запрос: {method}|{params}\nОтвет: {j_box_task}')
                        raise CommandError

                    # Находим в БД entityId коробки (он может быть в таблицах Спринтов или Бэклогов)
                    entity_id_in_backlogs_lst = Backlog.objects.filter(
                        backlog_id_cloud=j_cloud_scrum_task.get('result').get('entityId'))
                    if len(entity_id_in_backlogs_lst) > 0:  # Если entityId найден в Бэклогах
                        box_entity_id = entity_id_in_backlogs_lst[0].backlog_id_box
                    else:  # entityId НЕ найден в Бэклогах
                        entity_id_in_sprints_lst = Sprint.objects.filter(
                            sprint_id_cloud=j_cloud_scrum_task.get('result').get('entityId'))
                        if len(entity_id_in_sprints_lst) > 0:  # Если entityId найден в Спринтах
                            box_entity_id = entity_id_in_sprints_lst[0].sprint_id_box
                        else:  # Если entityId НЕ найден ни в Бэклогах, ни в Спринтах
                            logger.error(f'\t\tЗапрос на обновление задачи {j_cloud_task.get("title")!r} '
                                         f'в ключе скрама выполнен НЕ БУДЕТ! Не удалось найти entityId в БД.'
                                         f'Будет выполнена остановка выполнения команды.')
                            raise CommandError

                    # Находим в БД ID эпика для коробки
                    box_epic = Epic.objects.filter(epic_id_cloud=j_cloud_scrum_task.get('result').get('epicId'))
                    if len(box_epic) > 0:
                        box_epic_id = box_epic[0].epic_id_box
                    else:
                        box_epic_id = None

                    if box_entity_id:
                        # Обновляем задачу в коробке
                        method = 'tasks.api.scrum.task.update'
                        params = {
                            'id': j_box_task.get('result').get('task').get('id'),
                            'fields': {
                                'entityId': box_entity_id,
                                'storyPoints': j_cloud_scrum_task.get('result').get('storyPoints'),
                                'epicId': box_epic_id,
                                'sort': j_cloud_scrum_task.get('result').get('sort'),
                                'createdBy': scrum_task_created_by,
                                'modifiedBy': scrum_task_modified_by,
                            }
                        }
                        j_update_scrum_task_in_box = bitra_box.call(method=method, params=params)
                        if not j_update_scrum_task_in_box.get('result'):  # Проверка, что данные получены в запросе
                            logger.error(f'\t\tНе удалось ОБНОВИТЬ ЗАДАЧУ В КЛЮЧЕ СКРАМА В КОРОБКЕ! '
                                         f'Название задачи: {j_cloud_task.get("title")}'
                                         f'Задача из скрама: {i_scrum.scrum_title!r}. '
                                         f'Дальнейшее выполнение команды не имеет смысла.'
                                         f'Будет выполнена остановка выполнения команды.\n'
                                         f'Запрос: {method}|{params}\nОтвет: {j_update_scrum_task_in_box}')
                            raise CommandError

                    # Записываем данные о задаче в БД
                    scrum_task_rslt = ScrumTask.objects.update_or_create(
                        task_id_cloud=j_cloud_task.get('id'),
                        defaults={
                            'task_id_cloud': j_cloud_task.get('id'),
                            'task_id_box': j_box_task.get('result').get('task').get('id'),
                            'scrum_cloud_id': j_cloud_task.get('groupId'),
                            'scrum_box_id': j_box_task.get('result').get('task').get('groupId'),
                            'stage_id_cloud': j_cloud_task.get('stageId'),
                            'comments_count': j_cloud_task.get('commentsCount'),
                        }
                    )
                    if scrum_task_rslt[1]:  # Если задача была СОЗДАНА в БД
                        logger.success(f'\t\tЗадача {j_cloud_task.get("title")!r} СОЗДАНА в БД')
                    else:
                        logger.success(f'\t\tЗадача {j_cloud_task.get("title")!r} ОБНОВЛЕНА в БД')

                if i_cloud_tasks.get('next'):  # Если в ответе со списком задач есть параметр следующего батча
                    start_step = i_cloud_tasks.get('next')
                    logger.info(f'Ожидаем 3 секунды до следующего запроса 50 задач...')
                    time.sleep(3)
                else:  # Если это был крайний батч с задачами
                    logger.info(f'Тормозим цикл по задачам скрама: {i_scrum.scrum_title}')
                    break  # тормозим цикл

            logger.info(f'Ожидаем 3 секунды перед итерацией по следующему скраму...')
            time.sleep(3)
