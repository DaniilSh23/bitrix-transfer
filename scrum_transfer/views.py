import http
import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger
from rest_framework.views import APIView

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Backlog, Sprint, Epic


@csrf_exempt
def start_bitrix_cloud(request: WSGIRequest):
    """Вьюшка для старта приложения Битрикс (ОБЛАКО)"""

    if request.method == 'POST':
        # Регаем себе данные Битры
        # Ниже данные со страницы Битры при создании веб-приложухи, достаём их из БД.
        my_subdomain = Settings.objects.get(key='subdomain_cloud').value
        my_client_id = Settings.objects.get(key='client_id_cloud').value
        my_client_secret = Settings.objects.get(key='client_secret_cloud').value
        # Сохраняем access_token и refresh_token в БД
        Settings.objects.update_or_create(
            key='access_token_cloud',
            defaults={
                'key': 'access_token_cloud',
                'value': request.POST.get("auth[access_token]")
            }
        )
        Settings.objects.update_or_create(
            key='refresh_token_cloud',
            defaults={
                'key': 'refresh_token_cloud',
                'value': request.POST.get("auth[refresh_token]")
            }
        )
        # Создаём инстанс класса, который я переопределил в MyBitrix23.py
        bitra = Bitrix23(
            hostname=my_subdomain,
            client_id=my_client_id,
            client_secret=my_client_secret,
            access_token=request.POST.get("auth[access_token]"),
            refresh_token=request.POST.get("auth[refresh_token]"),
        )
        logger.info(f'Новые аксес и рефреш токены ОБЛАКО: {bitra._access_token, bitra._refresh_token}')
        return HttpResponse(f'Success', status=http.HTTPStatus.OK)
    else:
        return HttpResponse(f'Прости, мой друг, но {request.method} запрос не разрешён.🤷‍♂️', status=http.HTTPStatus.OK)


@csrf_exempt
def common_bitrix_cloud(request: WSGIRequest):
    """Вьюшка для получения запросов от Битрикса (ОБЛАКО)"""
    return HttpResponse(f'🆒Все круто, 😎классный {request.method} запрос!👌🏿', status=http.HTTPStatus.OK)


@csrf_exempt
def start_bitrix_box(request: WSGIRequest):
    """Вьюшка для старта приложения Битрикс (КОРОБКА)"""

    if request.method == 'POST':
        # Регаем себе данные Битры
        # Ниже данные со страницы Битры при создании веб-приложухи, достаём их из БД.
        my_subdomain = Settings.objects.get(key='subdomain_box').value
        my_client_id = Settings.objects.get(key='client_id_box').value
        my_client_secret = Settings.objects.get(key='client_secret_box').value
        # Сохраняем access_token и refresh_token в БД
        Settings.objects.update_or_create(
            key='access_token_box',
            defaults={
                'key': 'access_token_box',
                'value': request.POST.get("auth[access_token]")
            }
        )
        Settings.objects.update_or_create(
            key='refresh_token_box',
            defaults={
                'key': 'refresh_token_box',
                'value': request.POST.get("auth[refresh_token]")
            }
        )
        # Создаём инстанс класса, который я переопределил в MyBitrix23.py
        bitra = Bitrix23(
            hostname=my_subdomain,
            client_id=my_client_id,
            client_secret=my_client_secret,
            access_token=request.POST.get("auth[access_token]"),
            refresh_token=request.POST.get("auth[refresh_token]"),
        )
        logger.info(f'Новые аксес и рефреш токены КОРОБКА: {bitra._access_token, bitra._refresh_token, bitra._base_url_template}')
        return HttpResponse(f'Success', status=http.HTTPStatus.OK)
    else:
        return HttpResponse(f'Прости, мой друг, но {request.method} запрос не разрешён.🤷‍♂️', status=http.HTTPStatus.OK)


@csrf_exempt
def common_bitrix_box(request: WSGIRequest):
    """Вьюшка для получения запросов от Битрикса (КОРОБКА)"""
    return HttpResponse(f'🆒Все круто, 😎классный {request.method} запрос!👌🏿', status=http.HTTPStatus.OK)


class BacklogTransfer(APIView):
    """
    Вьюшка для трансфера бэклогов для скрамов.
    """
    def get(self, request,format=None):
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

        for i_numb, i_scrum in enumerate(scrum_objects):   # Берём каждый скрам
            logger.info(f'Обрабатываем скрам № {i_numb + 1}')

            # получаем бэклог скрама из облака
            logger.info(f'Запрос бэклога из облака для скрама: {i_scrum.scrum_title}')
            method = 'tasks.api.scrum.backlog.get'
            params = {
                'id': i_scrum.scrum_cloud_id,
            }
            i_backlog_cloud = bitra_cloud.call(method=method, params=params)
            if not i_backlog_cloud.get('result'):   # проверка, что запрос НЕ был успешным
                logger.warning(f'НЕ УДАЛСЯ запрос бэклога из ОБЛАКА для скрама: {i_scrum.scrum_title}.\n\n'
                               f'Ответ битрикса на запрос методом {method} с параметрами {params}:\n{i_backlog_cloud}')
                continue

            # Создаём бэклог в коробке
            logger.info(f'Запрос на создание бэклога в коробке для скрама: {i_scrum.scrum_title}')
            method = 'tasks.api.scrum.backlog.add'
            params = {
                'fields': {
                    'groupId': i_scrum.scrum_box_id,    # ID скрама
                    'createdBy': Settings.objects.get(key='worker_in_box_id').value,  # ID создателя
                },
            }
            i_backlog_box = bitra_box.call(method=method, params=params)
            if not i_backlog_box.get('result'):   # проверка, что запрос НЕ был успешным
                logger.warning(f'НЕ УДАЛСЯ запрос для создания бэклога в КОРОБКЕ для скрама: {i_scrum.scrum_title}.\n\n'
                               f'Ответ битрикса на запрос методом {method} с параметрами {params}:\n{i_backlog_box}')

                if i_backlog_box.get('error_description') == 'Backlog already added':   # если бэклог уже есть
                    logger.info(f'Запрос на получение бэклога из КОРОБКИ для скрама: {i_scrum.scrum_title}')
                    # Получаем бэклог скрама
                    method = 'tasks.api.scrum.backlog.get'
                    params = {
                        'id': i_scrum.scrum_box_id,
                    }
                    get_i_backlog_from_box = bitra_box.call(method=method, params=params)
                    if get_i_backlog_from_box.get('result'):
                        i_backlog_box = get_i_backlog_from_box
                    else:
                        logger.warning(
                            f'НЕ УДАЛСЯ запрос для ПОЛУЧЕНИЯ бэклога в КОРОБКЕ для скрама: {i_scrum.scrum_title}.\n\n'
                            f'Ответ битрикса на запрос методом {method} с параметрами {params}:\n{i_backlog_box}\n'
                            f'\t\t\tНу чтоже...тогда пропускаем и идём дальше по списку.')
                        continue
                else:
                    continue

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
        return HttpResponse(f'Запрос отработан. В админке записи в разделе Бэклоги соответствуют созданным '
                            f'бэклогам в коробке', status=http.HTTPStatus.OK)


class SprintTransfer(APIView):
    """
    Вьюшка для трансфера из облака в коробку битрикса спринтов для каждого скрама.
    """
    def get(self, request, format=None):
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
        for i_numb, i_scrum in enumerate(scrum_objects):   # итерируемся по скрамам
            logger.info(f'Скрам № {i_numb + 1}')
            # Получаем список спринтов из облака
            logger.info(f'Запрашиваем список спринтов из облака для скрама: {i_scrum.scrum_title}')
            method = 'tasks.api.scrum.sprint.list'
            params = {
                'filter': {
                    'GROUP_ID': i_scrum.scrum_cloud_id,
                },
            }
            sprints_lst = bitra_cloud.call(method=method, params=params)
            if not sprints_lst.get('result'):     # Если список спринтов не получен
                logger.warning(f'Запрос на получение из ОБЛАКА спринтов для скрама {i_scrum.scrum_title} НЕ УДАЛСЯ.\n\n'
                               f'Запрос {method} с параметрами {params}, ответ:\n{sprints_lst}')
                continue
            sprints_lst = sprints_lst.get('result')

            for j_numb, j_sprint in enumerate(sprints_lst):    # итерируемся по списку спринтов
                logger.info(f'Спринт № {j_numb + 1}')

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
                    continue

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
        return HttpResponse('Запрос выполнен. Записанные в коробке спринты '
                            'соответствуют списку из раздела Спринты в админке', status=http.HTTPStatus.OK)


class EpicTransfer(APIView):
    """
    Вьюшка для трансфера из облака в коробку эпиков для скрамов.
    """
    def get(self, request, format=None):
        logger.info('================НАЧИНАЕМ ТРАНСФЕР ЭПИКОВ! Это будет эпично...================')

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

            # Получаем список эпиков из облака
            logger.info(f'Получаем список эпиков из облака.')
            method = 'tasks.api.scrum.epic.list'
            params = {
                'filter': {
                    'GROUP_ID': i_scrum.scrum_cloud_id,
                },
            }
            epics_lst = bitra_cloud.call(method=method, params=params)
            if not epics_lst.get('result'):
                logger.warning(f'Неудачный запрос для получения списка эпиков! '
                               f'Возможно также, что список эпиков пуст.\n\n'
                               f'Запрос: {method}|{params}\nОтвет:{epics_lst}')
                continue

            for j_numb, j_epic in enumerate(epics_lst.get('result')):
                logger.info(f'\t\tЭпик № {j_numb + 1} | Скрам: {i_scrum.scrum_title}')

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
                    continue

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
        return HttpResponse('Запрос выполнен. Записанные в коробке эпики '
                            'соответствуют списку из раздела Эпики в админке', status=http.HTTPStatus.OK)


class ScrumTransferView(APIView):
    """
    Перенос скрамов из облака в коробку Битрикс.
    Здесь комплекс действий для этой цели.
    По итогу в коробке битры появляются скрамы и рассылаются приглашения на вступление их участникам.
    """
    # TODO: добавить обработку неудачных запросов к API Bitrix

    def get(self, request, format=None):
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

        '''Забираем скрамы из облака и записываем его в коробку, разослав и приглашения юзерам в коробке'''
        # ID sonet_group из облака, которые являются скрамами
        scrum_id_tpl = ('94', '102', '110', '82', '70', '62', '80', '86', '42', '60', '58',
                        '84', '64', '90', '72', '106', '52', '46', '78')
        # Получаем скрамы из облака
        method = 'sonet_group.get'
        params = {}
        method_rslt = bitra_cloud.call(method=method, params=params)
        counter = 0
        for i_sonet_group in method_rslt.get('result'):
            if i_sonet_group.get('ID') in scrum_id_tpl:
                counter += 1
                logger.info(f'Скрам № {counter}')

                # Получаем пользователей группы (скрама) из облака
                logger.info(f'Получаем пользователей группы (скрама) из облака')
                method = 'sonet_group.user.get'
                params = {
                    'ID': i_sonet_group.get('ID')  # ID группы (скрама)
                }
                method_rslt = bitra_cloud.call(method=method, params=params)
                i_scrum_users_lst = method_rslt.get('result')
                i_scrum_users_id_lst = [i_scrum_user.get('USER_ID') for i_scrum_user in i_scrum_users_lst]
                i_scrum_master_id = '28834' if '28834' in i_scrum_users_id_lst else '27662'

                # Получаем инфу о пользователях скрама из облака и находим их по мэйлу в коробке
                logger.info(f'Получаем инфу о пользователях скрама из облака и находим их по мэйлу в коробке (цикл)')
                for j_user_dct in i_scrum_users_lst:
                    logger.info(f"Юзер c ID в облаке {j_user_dct.get('USER_ID')}")
                    logger.info('Запрашиваем детальную инфу о польз. в облаке')
                    method = 'user.get'
                    params = {
                        'ID': j_user_dct.get('USER_ID'),    # ID пользователя в битре
                    }
                    method_rslt = bitra_cloud.call(method=method, params=params)    # Запрашиваем польз. в облаке
                    logger.info('Запрашиваем детальную инфу о польз. в коробке')
                    method = 'user.get'
                    params = {
                        'EMAIL': method_rslt.get('result')[0].get('EMAIL')
                    }
                    method_rslt = bitra_box.call(method=method, params=params)    # Запрашиваем польз. в коробке
                    j_user_dct['BOX_ID'] = method_rslt.get('result')[0].get('ID')   # Сохраняем ID юзера коробки
                    if j_user_dct.get('USER_ID') == i_scrum_master_id:   # Если итерируемый ID - скрам мастер
                        logger.info(f"Найден скрам-мастер (ID облака {j_user_dct.get('USER_ID')}, "
                                    f"ID коробки {j_user_dct['BOX_ID']})")
                        i_scrum_master_box_id = method_rslt.get('result')[0].get('ID')
                        # Создаём скрам в коробке, когда итерируемый юзер скрам-мастера
                        logger.info(f"Создаём скрам под названием {i_sonet_group.get('NAME')} в коробке")
                        method = 'sonet_group.create'
                        params = {
                            'NAME': i_sonet_group.get('NAME'),
                            'DESCRIPTION': i_sonet_group.get('DESCRIPTION'),
                            'ACTIVE': i_sonet_group.get('ACTIVE'),
                            'VISIBLE': i_sonet_group.get('VISIBLE'),
                            'OPENED': i_sonet_group.get('OPENED'),
                            'CLOSED': i_sonet_group.get('CLOSED'),
                            'SUBJECT_ID': i_sonet_group.get('SUBJECT_ID'),
                            'KEYWORDS': i_sonet_group.get('KEYWORDS'),
                            'SUBJECT_NAME': i_sonet_group.get('SUBJECT_NAME'),
                            'PROJECT': i_sonet_group.get('PROJECT'),
                            'IS_EXTRANET': i_sonet_group.get('IS_EXTRANET'),
                            'INITIATE_PERMS': 'E',  # Владелец или модеры могут приглашать в скрам
                            'SPAM_PERMS': 'K',  # Все члены имеют право на отправку сообщений в скрам
                            'SCRUM_MASTER_ID': i_scrum_master_box_id,   # ID скрам-мастера
                        }
                        method_rslt = bitra_box.call(method=method, params=params)
                        scrum_box_id = method_rslt.get('result')

                # Приглашаем в скрам пользователей (права можно проставить, после их вступления)
                logger.info(f"Приглашаем в скрам пользователей (права в скраме не проставляются).")
                method = 'sonet_group.user.invite'
                params = {
                    'GROUP_ID': scrum_box_id,
                    'USER_ID': list(map(lambda user_dct: user_dct.get('BOX_ID'), i_scrum_users_lst)),
                    'ROLE': f'Приглашаем Вас в проект: {i_sonet_group.get("NAME")}'
                }
                method_rslt = bitra_box.call(method=method, params=params)
        return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}', status=http.HTTPStatus.OK)


# TODO: закоментировал блок ниже, но оставляю его тут, на случай если понадобится обновить права юзеров в скраме
#                 # Обновляем скрам коробки пользователями и их правами
#                 scrum_moders_and_owner_lst = list(filter(lambda user_dct: user_dct.get('ROLE') == 'E' or user_dct.get('ROLE') == 'A', i_scrum_users_lst))
#                 scrum_other_users_lst = list(filter(lambda user_dct: user_dct.get('ROLE') == 'K', i_scrum_users_lst))
#                 # Приглашаем в скрам модераторов
#                 method = 'sonet_group.user.invite'
#                 params = {
#                     'GROUP_ID': scrum_box_id,
#                     'USER_ID': list(map(lambda user_dct: user_dct.get('BOX_ID'), scrum_moders_and_owner_lst)),
#                     'ROLE': 'E'
#                 }
#                 method_rslt = bitra_box.call(method=method, params=params)
#                 # Приглашаем в скрам обычных пользователей
#                 method = 'sonet_group.user.invite'
#                 params = {
#                     'GROUP_ID': scrum_box_id,
#                     'USER_ID': list(map(lambda user_dct: user_dct.get('BOX_ID'), scrum_other_users_lst)),
#                     'ROLE': 'K'
#                 }
#                 method_rslt = bitra_box.call(method=method, params=params)
#         return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}', status=http.HTTPStatus.OK)


class TestBitrixActions(APIView):
    """
    Тест каких-либо действий с АПИ Битрикса.
    Здесь комплекс методов с облаком и коробкой, которые объединены одной целью.
    """


class TestBtrxMethod(APIView):
    """Тест какого-либо метода битрикса"""

    def get(self, request, format=None):
        """Вьюшка для выполнения какого-либо метода АПИ Битрикса"""

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

        # # Записываю в сделку ID маркетплейсов
        # method = 'crm.deal.update'
        # params = {
        #     'id': 86920,  # Установил явно, ID сделки
        #     'fields': {
        #         'UF_CRM_1675152964610': [13268, 13274]  # Установил явно, ID маркетплеса(ов)
        #     },
        # }

        # # Создаём скрам
        # method = 'sonet_group.create'
        # params = {
        #     'NAME': 'Тестовый скрам',
        #     'DESCRIPTION': 'Тестовый скрам (описание)',
        #     'ACTIVE': 'Y',
        #     'VISIBLE': 'Y',
        #     'OPENED': 'Y',
        #     'CLOSED': 'N',
        #     'PROJECT': 'Y',
        #     'INITIATE_PERMS': 'E',  # Владелец или модеры могут приглашать в скрам
        #     'SPAM_PERMS': 'K',  # Все члены имеют право на отправку сообщений в скрам
        #     'SCRUM_MASTER_ID': 105,  # ID скрам-мастера
        # }

        # # Получаем группы (скрамы тоже среди них)
        # method = 'sonet_group.get'
        # params = {}

        # # Получаем пользователей группы (скрама)
        # method = 'sonet_group.user.get'
        # params = {
        #     'ID': 102   # ID группы (скрама)
        # }

        # # Получаем детальную инфу о пользователе
        # method = 'user.get'
        # params = {
        #     # 'ID': 105,    # ID пользователя в битре
        #     # 'EMAIL': 'd.shestakov@cfunalog.ru'
        # }

        # # Получаем доступные поля для ...
        # method = 'tasks.task.getFields'
        # params = {}

        # # Получаем бэклог скрама
        # method = 'tasks.api.scrum.backlog.get'
        # params = {
        #     'id': 28,
        # }

        # # Создаём бэклог скрама
        # method = 'tasks.api.scrum.backlog.add'
        # params = {
        #     'fields': {
        #         'groupId': 11,    # ID скрама
        #         'createdBy': 105,   # ID создателя
        #     },
        # }

        # # Удаляем бэклог
        # method = 'tasks.api.scrum.backlog.delete'
        # params = {
        #     'id': 21,   # ID бэклога
        # }

        # # Получаем список спринтов
        # method = 'tasks.api.scrum.sprint.list'
        # params = {
        #     'filter': {
        #         'GROUP_ID': 28,
        #     },
        # }

        # # Получаем спринт по ID
        # method = 'tasks.api.scrum.sprint.get'
        # params = {
        #     'id': 478,
        # }

        # # Получаем стадии канбана для спринта с ID ...
        # method = 'tasks.api.scrum.kanban.getStages'
        # params = {
        #     'sprintId': 37,
        # }

        # # Создаём стадию канбана в спринте
        # method = 'tasks.api.scrum.kanban.addStage'
        # params = {
        #     'fields': {
        #         'sprintId': 37,
        #         'name': 'TEST KABAN STAGE',
        #         # sort: sort,
        #         'type': 'NEW',  # NEW, WORK, FINISH
        #         # color: color,
        #     },
        # }

        # # Добавляем задачу в стадию канбана
        # method = 'tasks.api.scrum.kanban.addTask'
        # params = {
        #     'sprintId': 37,
        #     'taskId': 118,
        #     'stageId': 48,
        # }

        # # Создаём спринт в скраме
        # method = 'tasks.api.scrum.sprint.add'
        # params = {
        #     'fields': {
        #         'groupId': 28,
        #         'name': 'TEST SPRINT',
        #         'dateStart': '2021-11-22T00:00:00+02:00',
        #         'dateEnd': '2021-11-23T00:00:00+02:00',
        #         'status': 'active',
        #         'createdBy': 105,
        #         'sort': 1,
        #     },
        # }

        # # Получаем список эпиков
        # method = 'tasks.api.scrum.epic.list'
        # params = {
        #     'filter': {
        #         'GROUP_ID': 25,
        #     },
        # }

        # # Создаём эпик
        # method = 'tasks.api.scrum.epic.add'
        # params = {
        #     'fields': {
        #         'groupId': 25,
        #         'name': 'TEST EPIC',
        #         'description': "DESCRIPTION FOR TEST EPIC",
        #         'createdBy': 105,
        #         'color': '#e3f299',
        #     },
        # }

        # # Удаляем эпик
        # method = 'tasks.api.scrum.epic.delete'
        # params = {
        #     'id': 3,
        # }

        # # Создаём задачу в битриксе
        # method = 'tasks.task.add'
        # params = {
        #     'fields': {
        #                     'PARENT_ID': None, 'TITLE': 'Тест создания задачи',
        #                     'DESCRIPTION': 'тестовое описание', 'MARK': None, 'PRIORITY': 1,
        #                     'STATUS': 3, 'MULTITASK': 'N', 'NOT_VIEWED': 'N',
        #                     'REPLICATE': 'N', 'GROUP_ID': 28, 'STAGE_ID': None,
        #                     'CREATED_BY': 105, 'CREATED_DATE': "2023-03-13T15:53:31+03:00", 'RESPONSIBLE_ID': 105,
        #                     'ACCOMPLICES': None, 'AUDITORS': None, 'CHANGED_BY': 105,
        #                     'CHANGED_DATE': "2023-03-13T15:53:31+03:00", 'STATUS_CHANGED_BY': 105,
        #                     'STATUS_CHANGED_DATE': "2023-03-13T15:53:31+03:00", 'CLOSED_BY': None,
        #                     'CLOSED_DATE': None, 'ACTIVITY_DATE': "2023-03-14T15:42:26+03:00",
        #                     'DATE_START': None, 'DEADLINE': None, 'ALLOW_CHANGE_DEADLINE': None,
        #                     'ALLOW_TIME_TRACKING': None, 'TASK_CONTROL': None, 'ADD_IN_REPORT': None,
        #                     'START_DATE_PLAN': None, 'END_DATE_PLAN': None, 'TIME_ESTIMATE': 0,
        #                     'TIME_SPENT_IN_LOGS': None, 'MATCH_WORK_TIME': 'N',
        #                     # 'FORUM_TOPIC_ID': 0, 'FORUM_ID': 0, 'SITE_ID': 0,
        #                     'SUBORDINATE': 'N', 'FAVORITE': 'N',
        #                     'EXCHANGE_MODIFIED': None, 'EXCHANGE_ID': None,
        #                     'OUTLOOK_VERSION': 8, 'VIEWED_DATE': "2023-03-14T15:42:26+03:00", 'SORTING': None,
        #                     'DURATION_PLAN': 0, 'DURATION_FACT': None, 'DURATION_TYPE': 'days',
        #                     'IS_MUTED': 'N', 'IS_PINNED': 'N', 'IS_PINNED_IN_GROUP': 'N',
        #                     'CHECKLIST': None, 'UF_CRM_TASK': None, 'UF_MAIL_MESSAGE': None,
        #                 }
        # }

        # # Обновляем задачу в ключе скрама
        # method = 'tasks.api.scrum.task.update'
        # params = {
        #     'id': 118,
        #     'fields': {
        #         "entityId": 35,
        #         'storyPoints': 18,
        #         'epicId': None,
        #         "sort": 13,
        #     }
        # }

        # # Получаем список задач Битрикса
        # method = 'tasks.task.list'
        # params = {
        #     'filter': {
        #         'GROUP_ID': 28,    # Для группы(скрама) с нужным ID
        #     },
        #     # 'start': 50,    # Выводить задачи, начиная с 50 записи(это для следующих 50)
        # }

        # # Получаем инфу о задачи скрама по её id == 118
        # method = 'tasks.api.scrum.task.get'
        # params = {
        #     'id': 118,
        # }

        # Получаем комментарии к задаче
        method = 'task.commentitem.getlist'
        params = {
            'TASKID': 118
        }

        # # Создание комментария к задаче
        # method = 'task.commentitem.add'
        # params = {
        #     'TASKID': 118,
        #     'FIELDS': {
        #         'AUTHOR_ID': 105,
        #         'POST_MESSAGE': "Тестовый текст комментария.",
        #         # 'UF_FORUM_MESSAGE_DOC': ['список файлов с диска, для прикрепления вида ["n123", ...]'],
        #     },
        # }

        # method_rslt = bitra_cloud.call(method=method, params=params)
        method_rslt = bitra_box.call(method=method, params=params)
        print('=' * 10, f'РЕЗУЛЬТАТ МЕТОДА {method}', '=' * 10, f'\n\n{method_rslt}')
        return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}', status=http.HTTPStatus.OK)
