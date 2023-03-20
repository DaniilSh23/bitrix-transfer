from django.core.management import BaseCommand

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, BitrixUsers


class Command(BaseCommand):
    """
    Команда для создания юзеров битры в БД
    """
    def handle(self, *args, **options):
        self.stdout.write('Начинаем запись юзеров битры в БД.')

        # Создаём инстанс битры ОБЛАКО
        bitra_cloud = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_cloud").value,
            client_id=Settings.objects.get(key="client_id_cloud").value,
            client_secret=Settings.objects.get(key="client_secret_cloud").value,
            access_token=Settings.objects.get(key="access_token_cloud").value,
            refresh_token=Settings.objects.get(key="refresh_token_cloud").value,
        )
        bitra_cloud.refresh_tokens()
        # Создаём инстанс битры КОРОБКА (НЕ ЗАБЫТЬ ОБНОВИТЬ ТОКЕНЫ)
        bitra_box = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_box").value,
            client_id=Settings.objects.get(key="client_id_box").value,
            client_secret=Settings.objects.get(key="client_secret_box").value,
            access_token=Settings.objects.get(key="access_token_box").value,
            refresh_token=Settings.objects.get(key="refresh_token_box").value,
        )
        scrums_lst = Scrums.objects.all()
        for i_scrum in scrums_lst:
            self.stdout.write(f'Обрабатываем скрам: {i_scrum.scrum_title}')
            method = 'sonet_group.user.get'
            params = {
                'ID': i_scrum.scrum_cloud_id
            }
            scrum_users_method_rslt = bitra_cloud.call(method=method, params=params)
            users_count = 0
            for j_user_dct in scrum_users_method_rslt.get('result'):
                self.stdout.write(f"Запрашиваем инфу о юзере с ID {j_user_dct.get('USER_ID')} в облаке")
                method = 'user.get'
                params = {
                    'ID': j_user_dct.get('USER_ID'),  # ID пользователя в битре
                }
                cloud_user_method_rslt = bitra_cloud.call(method=method, params=params)  # Запрашиваем польз. в облаке
                self.stdout.write(f"Запрашиваем инфу о юзере с EMAIL {cloud_user_method_rslt.get('result')[0].get('EMAIL')} в коробке")
                method = 'user.get'
                params = {
                    'EMAIL': cloud_user_method_rslt.get('result')[0].get('EMAIL')
                }
                box_user_method_rslt = bitra_box.call(method=method, params=params)  # Запрашиваем польз. в коробке
                BitrixUsers.objects.get_or_create(
                    user_id_cloud=j_user_dct.get('USER_ID'),
                    defaults={
                        'user_id_cloud': j_user_dct.get('USER_ID'),
                        'user_id_box': box_user_method_rslt.get('result')[0].get('ID'),
                        'email': cloud_user_method_rslt.get('result')[0].get('EMAIL'),
                        'name': f"{cloud_user_method_rslt.get('result')[0].get('NAME')} "
                                f"{cloud_user_method_rslt.get('result')[0].get('LAST_NAME')}",
                    }
                )
                users_count += 1
                self.stdout.write(self.style.SUCCESS(f'Обработан юзер скрама {j_user_dct.get("USER_ID")}. '
                                                     f'Итого проработано {users_count} юзеров.'))


