from django.core.management import BaseCommand

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums


class Command(BaseCommand):
    """
    Команда для создания скрамов БД
    """

    def handle(self, *args, **options):
        self.stdout.write('Начинаем запись скрамов в БД.')

        # Создаём инстанс битры ОБЛАКО
        bitra_cloud = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_cloud").value,
            client_id=Settings.objects.get(key="client_id_cloud").value,
            client_secret=Settings.objects.get(key="client_secret_cloud").value,
            access_token=Settings.objects.get(key="access_token_cloud").value,
            refresh_token=Settings.objects.get(key="refresh_token_cloud").value,
        )
        bitra_cloud.refresh_tokens()
        # Получаем скрамы из облака
        method = 'sonet_group.get'
        params = {}
        cloud_scrums = bitra_cloud.call(method=method, params=params)

        scrum_id_dct = {'94': '12', '102': '11', '110': '9', '82': '16', '70': '20', '62': '22', '80': '17', '86': '14',
                        '60': '23', '58': '24', '84': '15', '64': '21', '90': '14', '72': '19', '106': '10',
                        '46': '25', '78': '18'}
        count = 0
        for i_sonet_group in cloud_scrums.get('result'):
            if i_sonet_group.get('ID') in scrum_id_dct.keys():
                Scrums.objects.get_or_create(
                    scrum_cloud_id=i_sonet_group.get('ID'),
                    defaults={
                        'scrum_cloud_id': i_sonet_group.get('ID'),
                        'scrum_box_id': scrum_id_dct.get(i_sonet_group.get('ID')),
                        'scrum_title': i_sonet_group.get('NAME'),
                    }
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Записан|Обновлён скрам {i_sonet_group.get("ID")}. '
                                                     f'Итого проработано {count} записей.'))


