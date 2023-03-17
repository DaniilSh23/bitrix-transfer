import http
import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger
from rest_framework.views import APIView

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings


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


class TestBtrxActionsView(APIView):
    """
    Тест каких-либо действий с АПИ Битрикса.
    Здесь комплекс методов с облаком и коробкой, которые объединены одной целью.
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
                    method = 'user.get'
                    logger.info('Запрашиваем детальную инфу о польз. в облаке')
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

        # # Создаём инстанс битры КОРОБКА
        # bitra_box = Bitrix23(
        #     hostname=Settings.objects.get(key="subdomain_box").value,
        #     client_id=Settings.objects.get(key="client_id_box").value,
        #     client_secret=Settings.objects.get(key="client_secret_box").value,
        #     access_token=Settings.objects.get(key="access_token_box").value,
        #     refresh_token=Settings.objects.get(key="refresh_token_box").value,
        # )
        # bitra_box.refresh_tokens()

        # # Записываю в сделку ID маркетплейсов
        # method = 'crm.deal.update'
        # params = {
        #     'id': 86920,  # Установил явно, ID сделки
        #     'fields': {
        #         'UF_CRM_1675152964610': [13268, 13274]  # Установил явно, ID маркетплеса(ов)
        #     },
        # }

        # # Получаем группы (скрамы тоже среди них)
        # method = 'sonet_group.get'
        # params = {}

        # Получаем пользователей группы (скрама)
        method = 'sonet_group.user.get'
        params = {
            'ID': 102   # ID группы (скрама)
        }

        # # Получаем детальную инфу о пользователе
        # method = 'user.get'
        # params = {
        #     # 'ID': 105,    # ID пользователя в битре
        #     # 'EMAIL': 'd.shestakov@cfunalog.ru'
        # }

        method_rslt = bitra_cloud.call(method=method, params=params)
        # method_rslt = bitra_box.call(method=method, params=params)
        print('=' * 10, f'РЕЗУЛЬТАТ МЕТОДА {method}', '=' * 10, f'\n\n{method_rslt}')
        return HttpResponse(f'{json.dumps(method_rslt, indent=4, ensure_ascii=False)}', status=http.HTTPStatus.OK)
