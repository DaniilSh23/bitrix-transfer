from django.core.management import BaseCommand
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums


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

        cycle_flag = True
        scrum_objects = Scrums.objects.all()
        for i_numb, i_scrum in enumerate(scrum_objects):
            logger.info(f'Скрам №{i_numb + 1}|{i_scrum.scrum_title}')

            start_step = None
            while cycle_flag:
                # Запрашиваем задачи скрама из облака
                method = 'tasks.task.list'
                params = {
                    'filter': {
                        'GROUP_ID': i_scrum.scrum_cloud_id,  # ID группы(скрама)
                    },
                    'start': start_step,  # Выводить задачи, начиная с ...(параметр next в ответе)
                }
                i_cloud_tasks = bitra_cloud.call(method=method, params=params)
                for j_cloud_task in i_cloud_tasks.get('result').get('tasks'):
                    # Запрашиваем инфу о задаче в ключе скрама
                    method = 'tasks.api.scrum.task.get'
                    params = {'id': j_cloud_task.get('id')}
                    j_cloud_scrum_task = bitra_cloud.call(method=method, params=params)

                    # Создаём задачу в коробке
                    method = 'tasks.task.add'
                    params = {  # TODO: доделать
                        'ID': 0, 'PARENT_ID': 0, 'TITLE': 0,
                        'DESCRIPTION': 0, 'MARK': 0, 'PRIORITY': 0,
                        'STATUS': 0, 'MULTITASK': 0, 'NOT_VIEWED': 0,
                        'REPLICATE': 0, 'GROUP_ID': 0, 'STAGE_ID': 0,
                        'CREATED_BY': 0, 'CREATED_DATE': 0, 'RESPONSIBLE_ID': 0,
                        'ACCOMPLICES': 0, 'AUDITORS': 0, 'CHANGED_BY': 0,
                        'CHANGED_DATE': 0, 'STATUS_CHANGED_BY': 0, 'CLOSED_BY': 0,
                        'CLOSED_DATE': 0, 'DATE_START': 0, 'DEADLINE': 0,
                        'START_DATE_PLAN': 0, 'END_DATE_PLAN': 0, 'TIME_ESTIMATE': 0,
                        'TIME_SPENT_IN_LOGS': 0, 'MATCH_WORK_TIME': 0, 'FORUM_TOPIC_ID': 0,
                        'FORUM_ID': 0, 'SITE_ID': 0, 'SUBORDINATE': 0,
                        'FAVORITE': 0, 'EXCHANGE_MODIFIED': 0, 'EXCHANGE_ID': 0,
                        'OUTLOOK_VERSION': 0, 'VIEWED_DATE': 0, 'SORTING': 0,
                        'DURATION_PLAN': 0, 'DURATION_FACT': 0, 'CHECKLIST': 0,
                        'DURATION_TYPE': 0, 'UF_CRM_TASK': 0, 'UF_MAIL_MESSAGE': 0,
                        'IS_MUTED': 0, 'IS_PINNED': 0, 'IS_PINNED_IN_GROUP': 0, 'SERVICE_COMMENTS_COUNT': 0,
                    }
                    j_box_task = bitra_box.call(method=method, params=params)
                    # Обновляем задачу в коробке
                    # TODO: подобрать коробочный entityId из таблиц бэклогов или спринтов
                    method = 'tasks.api.scrum.task.get'
                    params = {  # TODO: доделать
                        'id': 0,
                        'fields': {
                            'entityId': 0,
                            'storyPoints': 0,
                            'epicId': 0,
                            'sort': 0,
                            'createdBy': 0,
                            'modifiedBy': 0,
                        }
                    }
                    # TODO: записать задачу в БД
                if i_cloud_tasks.get('next'):
                    start_step = i_cloud_tasks.get('next')
                else:
                    cycle_flag = False
