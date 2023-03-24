from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, BitrixUsers


class Command(BaseCommand):
    """
    Перенос скрамов из облака в коробку Битрикс.
    Здесь комплекс действий для этой цели.
    По итогу в коробке битры появляются скрамы и рассылаются приглашения на вступление их участникам.
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

        # Получаем скрамы из облака
        method = 'sonet_group.get'
        params = {}
        sonet_groups_cloud = bitra_cloud.call(method=method, params=params)
        if not sonet_groups_cloud.get('result'):
            logger.error(f'Не удалось получить список скрамов.\nЗапрос: {method}|{params}\nОтвет: {sonet_groups_cloud}')
            raise CommandError

        counter = 0
        for i_sonet_group in sonet_groups_cloud.get('result'):

            # Пробуем найти скрам в БД
            try:
                i_scrum = Scrums.objects.get(scrum_cloud_id=i_sonet_group.get('ID'))
                counter += 1
                logger.info(f'Найден скрам № {counter}: {i_sonet_group.get("NAME")}')
            except Exception as error:
                logger.info(f'Скрам не найден в БД. Но на всякий случай вот текст ошибки: {error}\n'
                            f'Также вот искомый в БД ID скрама(облако): {i_sonet_group.get("ID")}')
                # input('\tENTER -- пропустить\n\tCTRL+C -- остановит команду')
                continue

            # Проверка, что скрам уже создавался или помечен как архивный
            if i_scrum.scrum_box_id:
                logger.info(f'Скрам {i_scrum.scrum_title!r} уже был создан ранее. Пропускаем его...')
                continue
            elif i_scrum.is_archived:
                logger.info(f'Скрам {i_scrum.scrum_title!r} находится в архиве. Пропускаем его...')
                continue

            # Получаем пользователей скрама из облака
            logger.info(f'Получаем пользователей скрама из облака')
            method = 'sonet_group.user.get'
            params = {
                'ID': i_sonet_group.get('ID')  # ID группы (скрама)
            }
            scrum_users = bitra_cloud.call(method=method, params=params)
            if not scrum_users.get('result'):
                logger.error(f'Не удалось получить список юзеров для скрама: {i_sonet_group.get("NAME")}.\n'
                             f'Запрос: {method}|{params}\nОтвет: {scrum_users}')
                raise CommandError

            # Получаем инфу о пользователях скрама из облака и находим их по мэйлу в коробке
            box_scrum_users_lst = []
            for j_user in scrum_users.get('result'):
                logger.info(f"Юзер c ID в облаке {j_user.get('USER_ID')}")

                # Запрашиваем детальную инфу о юзере в облаке
                method = 'user.get'
                params = {
                    'ID': j_user.get('USER_ID'),  # ID пользователя в битре
                }
                user_detail_from_cloud = bitra_cloud.call(method=method, params=params)
                if not user_detail_from_cloud.get('result'):
                    logger.error(f'Не удалось получить инфу о юзере из ОБЛАКА. USER_ID: {j_user.get("USER_ID")}.\n'
                                 f'Запрос: {method}|{params}\nОтвет: {user_detail_from_cloud}')
                    raise CommandError

                # Запрашиваем детальную инфу о юзере в коробке
                method = 'user.get'
                params = {
                    'EMAIL': user_detail_from_cloud.get('result')[0].get('EMAIL')
                }
                user_detail_from_box = bitra_box.call(method=method, params=params)  # Запрашиваем польз. в коробке
                if not user_detail_from_cloud.get('result'):
                    logger.error(f'Не удалось получить инфу о юзере из КОРОБКИ. EMAIL: {j_user.get("EMAIL")}.\n'
                                 f'Запрос: {method}|{params}\nОтвет: {user_detail_from_box}')
                    raise CommandError

                # Добавляем коробочный ID юзера в список для последующего инвайта в скрам
                box_scrum_users_lst.append(user_detail_from_cloud.get('result')[0].get('ID'))

                # Обновляем или создаём запись о юзере в БД
                user_db_write_rslt = BitrixUsers.objects.update_or_create(
                    email=user_detail_from_cloud.get('result')[0].get('EMAIL'),
                    defaults={
                        "user_id_cloud": user_detail_from_cloud.get('result')[0].get('ID'),
                        "user_id_box": user_detail_from_box.get('result')[0].get('ID'),
                        "email": user_detail_from_cloud.get('result')[0].get('EMAIL'),
                        "name": f"{user_detail_from_cloud.get('result')[0].get('NAME')} "
                                f"{user_detail_from_cloud.get('result')[0].get('LAST_NAME')}",
                    }
                )
                logger.success(f"Пользователь {user_detail_from_cloud.get('result')[0].get('EMAIL')} "
                               f"{'создан' if user_db_write_rslt[1] else 'обновлён'} в БД.")

                # Проверка, что итерируемый юзер скрам-мастер
                if j_user.get('USER_ID') == i_scrum.scrum_master_id_cloud:
                    logger.info(f'Найден скрам мастер для скрама: {i_sonet_group.get("NAME")}')
                    # Создаём скрам в коробке
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
                        'SCRUM_MASTER_ID': user_detail_from_box.get('result')[0].get('ID'),  # ID скрам-мастера
                    }
                    scrum_create_rslt = bitra_box.call(method=method, params=params)
                    if not scrum_create_rslt.get('result'):
                        logger.error(f'Не удалось создать скрам в коробке. Скрам: {i_sonet_group.get("NAME")}.\n'
                                     f'Запрос: {method}|{params}\nОтвет: {scrum_create_rslt}')
                        raise CommandError

                    # Обновляем запись скрама в БД
                    i_scrum.scrum_box_id = scrum_create_rslt.get('result')
                    i_scrum.scrum_master_id_box = user_detail_from_box.get('result')[0].get('ID')
                    i_scrum.scrum_title = i_sonet_group.get('NAME')
                    i_scrum.save()
                    logger.success(f"Скрам {i_sonet_group.get('NAME')} обновлён БД и создан в коробке")

            # Приглашаем в скрам пользователей (права можно проставить, после их вступления)
            method = 'sonet_group.user.invite'
            params = {
                'GROUP_ID': i_scrum.scrum_box_id,
                'USER_ID': box_scrum_users_lst,
                'MESSAGE': f'Приглашаем Вас в проект: {i_sonet_group.get("NAME")}'
            }
            invite_users_rslt = bitra_box.call(method=method, params=params)
            if invite_users_rslt.get('result') is None:
                logger.error(f'Не удалось пригласить юзеров из списка: {box_scrum_users_lst} '
                             f'в скрам: {i_sonet_group.get("NAME")}.\n'
                             f'Запрос: {method}|{params}\nОтвет: {invite_users_rslt}')
                raise CommandError
