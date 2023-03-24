from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings


class Command(BaseCommand):
    """
    Команда для удаления задач скрама.
    В начале цикла while True мы получаем список задач.
    Там в параметр GROUP_ID нужно указать ID скрама, задачи которого должны быть удалены.
    """
    def handle(self, *args, **options):

        # Создаём инстанс битры КОРОБКА
        bitra_box = Bitrix23(
            hostname=Settings.objects.get(key="subdomain_box").value,
            client_id=Settings.objects.get(key="client_id_box").value,
            client_secret=Settings.objects.get(key="client_secret_box").value,
            access_token=Settings.objects.get(key="access_token_box").value,
            refresh_token=Settings.objects.get(key="refresh_token_box").value,
        )
        # bitra_box.refresh_tokens()

        delete_tasks_counter = 0
        start_step = 0
        while True:
            # Получаем список задач Битрикса
            method = 'tasks.task.list'
            params = {
                'filter': {
                    'GROUP_ID': 23,    # Для группы(скрама) с нужным ID
                },
                'start': start_step,    # Выводить задачи, начиная с 50 записи(это для следующих 50)
            }
            tasks_lst = bitra_box.call(method=method, params=params)

            if tasks_lst.get('result'):
                for i_task in tasks_lst.get('result').get('tasks'):

                    # Удаляем задачу из коробки
                    method = 'tasks.task.delete'
                    params = {
                        'taskId': i_task.get('id')
                    }
                    task_delete_rslt = bitra_box.call(method=method, params=params)
                    if task_delete_rslt.get('result'):
                        logger.success(f'Успешное удаление задачи с ID {i_task.get("id")}')
                        delete_tasks_counter += 1
                    else:
                        logger.warning(f'Не удалось удалить задачу с ID {i_task.get("id")}.\n'
                                       f'Запрос: {method} | {params}.\nОтвет: {task_delete_rslt}')
            else:
                logger.error(f'Не удалось получить список задач.\nЗапрос: {method} | {params}\nОтвет: {tasks_lst}')
                raise CommandError

            # Проверка, есть ли следующая пачка из 50 задач
            if not tasks_lst.get('next'):
                break
            else:
                start_step = tasks_lst.get('next')
        logger.success(f'Удаление задач завершено! Удалено: {delete_tasks_counter} задач из {tasks_lst.get("total")}')