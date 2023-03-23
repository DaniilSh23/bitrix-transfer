import time

from django.core.management import BaseCommand, CommandError
from loguru import logger

from scrum_transfer.MyBitrix23 import Bitrix23
from scrum_transfer.models import Settings, Sprint, KanbanStages, ScrumTask


class Command(BaseCommand):
    """
    Команда для трансфера стадий канбанов в спринтах скрама.
    """
    def handle(self, *args, **options):
        self.stdout.write('Старт трансфера стадий канбанов!')

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

        all_sprints = Sprint.objects.all()
        for i_numb, i_sprint in enumerate(all_sprints):
            logger.info(f'Обработка спринта № {i_numb + 1} из {len(all_sprints)}')
            # Задержка каждые 15 спринтов
            if (i_numb + 1) % 15 == 0:
                logger.info(f'Пауза между обработкой спринтов 3 сек.')
                time.sleep(3)

            # Получаем из облака стадии канбана для спринта
            method = 'tasks.api.scrum.kanban.getStages'
            params = {
                'sprintId': i_sprint.sprint_id_cloud,
            }
            kanban_stages = bitra_cloud.call(method, params)
            if not kanban_stages.get('result'):
                logger.error(f'Неудачный запрос для получения стадий канбана '
                             f'для спринта cloud_id == {i_sprint.sprint_id_cloud}.'
                             f'Запрос: {method}|{params}\nОтвет: {kanban_stages}')
                raise CommandError
            input(f'СТАДИИ КАНБАНА: {kanban_stages}')
            for j_numb, j_stage in enumerate(kanban_stages.get('result')):
                logger.info(f'\tОбработка стадии канбана № {j_numb + 1} | {j_stage.get("name")}')

                # Проверка, что стадия канбана ранее создавалась в коробке
                stage_exist_lst = KanbanStages.objects.filter(stages_id_cloud=j_stage.get("id"))
                if len(stage_exist_lst) > 0:
                    logger.info(f'\tСтадия ранее была создана в коробке. Пропускаем её')
                    continue

                # Создаём стадию канбана в коробке
                method = 'tasks.api.scrum.kanban.addStage'
                params = {
                    'fields': {
                        'sprintId': i_sprint.sprint_id_box,
                        'name': j_stage.get('name'),
                        # sort: sort,
                        'type': j_stage.get('type'),  # NEW, WORK, FINISH
                        # color: color,
                    },
                }
                kanban_stage_box = bitra_box.call(method, params)
                if not kanban_stage_box.get('result'):
                    logger.error(f'Неудачный запрос для создания стадии канбана в коробке '
                                 f'для спринта box_id == {i_sprint.sprint_id_box}.'
                                 f'Запрос: {method}|{params}\nОтвет: {kanban_stages}')
                    raise CommandError
                input(f'СОЗДАНИЕ В КОРОБКЕ СТАДИИ КАНБАНА: {kanban_stage_box}')
                # Записываем данные о стадии канбана в БД
                kanban_write_rslt = KanbanStages.objects.update_or_create(
                    stages_id_cloud=j_stage.get('id'),
                    defaults={
                        'sprint_id_cloud': i_sprint.sprint_id_cloud,
                        'sprint_id_box': i_sprint.sprint_id_box,
                        'stages_id_cloud': j_stage.get('id'),
                        'stages_id_box': kanban_stage_box.get('result'),
                    }
                )
                logger.success(f'\tУспешное {"создание" if kanban_write_rslt[1] else "обновлени"} стадии канбана в БД')

                # Добавляем задачи в стадию канбана
                kanban_stage_tasks = ScrumTask.objects.filter(stage_id_cloud=j_stage.get('id'))
                for k_numb, k_task in enumerate(kanban_stage_tasks):
                    logger.info(f'\t\tДобавление задачи № {k_numb + 1} в стадию {j_stage.get("name")}')

                    # Проверка, что задача ранее была добавлена в стадию
                    if k_task.stage_id_box:
                        logger.info(f'\t\tЗадача уже была добавлена в стадию канбана. Пропускаем её.')
                        continue

                    method = 'tasks.api.scrum.kanban.addTask'
                    params = {
                        'sprintId': i_sprint.sprint_id_box,
                        'taskId': k_task.task_id_box,
                        'stageId': kanban_stage_box.get('result'),
                    }
                    task_in_kanban_stage = bitra_box.call(method, params)
                    if not task_in_kanban_stage.get('result'):
                        logger.error(f'Неудачный запрос для добавления задачи в стадию канбана в коробке '
                                     f'для спринта с box_id == {i_sprint.sprint_id_box}.'
                                     f'Запрос: {method}|{params}\nОтвет: {kanban_stages}')
                        raise CommandError
                    input(f'ДОБАВЛЕНИЕ ЗАДАЧИ В СТАДИЮ КАНБАНА: {task_in_kanban_stage}')
                    # Обновляем задачу в БД
                    k_task.stage_id_box = kanban_stage_box.get('result')
                    k_task.save()
                    logger.success(f'Успешное обновление stage_id_box задачи в БД')



