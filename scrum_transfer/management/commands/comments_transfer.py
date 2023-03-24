import time

from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Scrums, Backlog, BitrixUsers, Sprint, ScrumTask, TaskComment


class Command(BaseCommand):
    """
    Команда для трансфера комментов к здачам скрама.
    """

    def handle(self, *args, **options):
        self.stdout.write('Старт трансфера комментов к задачам!')

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

        all_tasks = ScrumTask.objects.all()
        tasks_length = len(all_tasks)
        for i_numb, i_task in enumerate(all_tasks):
            logger.info(f'Обрабатываем комменты задачи  {i_numb + 1} из {tasks_length}')

            if (i_numb + 1) % 20 == 0:
                logger.info(f'Делаем паузу на 3 сек.(пауза каждые 20 задач)')
                time.sleep(3)

            # Берём из облака список комментов для этой задачи
            method = 'task.commentitem.getlist'
            params = {
                'TASKID': i_task.task_id_cloud
            }
            cloud_comments_lst = bitra_cloud.call(method=method, params=params)
            if cloud_comments_lst.get('result') is None:
                logger.error(f'Не удалось получить список комментариев для задачи '
                             f'с task_id_cloud=={i_task.task_id_cloud}. '
                             f'Команда будет остановлена!\n'
                             f'Запрос: {method}|{params}\nОтвет: {cloud_comments_lst}')
                raise CommandError

            for j_comment in cloud_comments_lst.get('result'):

                # Проверка на существование коммента
                comment_already_exist = TaskComment.objects.filter(comment_id_cloud=j_comment.get('ID'))
                if len(comment_already_exist) > 0:
                    logger.info(f'Комментарий ранее был создан! Пропускаем его...')
                    continue

                # Получаем автора коммента
                try:
                    comment_author = BitrixUsers.objects.get(user_id_cloud=j_comment.get('AUTHOR_ID'))
                except Exception as error:
                    logger.warning(f'Не удалось получить из БД ID юзера(коробка). '
                                   f'ID юзера: {j_comment.get("AUTHOR_ID")} Текст ошибки:{error}. Пропускаем коммент.')
                    continue

                # Создаём в коробке комментарий к задаче
                method = 'task.commentitem.add'
                params = {
                    'TASKID': i_task.task_id_box,
                    'FIELDS': {
                        'AUTHOR_ID': comment_author.user_id_box,
                        'POST_MESSAGE': j_comment.get('POST_MESSAGE'),
                        # 'UF_FORUM_MESSAGE_DOC': ['список файлов с диска, для прикрепления вида ["n123", ...]'],
                    },
                }
                box_comment_creation_rslt = bitra_box.call(method=method, params=params)
                if not box_comment_creation_rslt.get('result'):
                    logger.error(f'Неудачный запрос для создания коммента в коробке. '
                                 f'Команда будет остановлена!\n'
                                 f'Запрос: {method}|{params}\nОтвет: {box_comment_creation_rslt}')
                    input('CTRL+C -- прекратить выполнение команды | ENTER -- пропустить')
                    continue
                    # raise CommandError

                # Создаём в БД запись о новом комменте
                comment_in_db = TaskComment.objects.update_or_create(
                    comment_id_cloud=j_comment.get('ID'),
                    defaults={
                        'comment_id_cloud': j_comment.get('ID'),
                        'comment_id_box': box_comment_creation_rslt.get('result'),
                        'author_id_cloud': j_comment.get('AUTHOR_ID'),
                        'author_id_box': comment_author.user_id_box,
                        'author_mail': comment_author.email,
                        'files_in_comments': j_comment.get('UF_FORUM_MESSAGE_DOC'),
                    }
                )
                logger.success(f'Комментарий {"создан" if comment_in_db[1] else "обновлён"} в БД!')
                # logger.info(f'Пауза между обработкой комментариев 0.5 секунды.')
                # time.sleep(0.5)
