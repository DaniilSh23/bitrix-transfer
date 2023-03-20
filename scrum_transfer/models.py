from django.db import models


class Settings(models.Model):
    """
    Модель для настроек провекта. Хранилище key-value.
    Здесь храним разные параметры, например access и refresh токены для веб-приложения битрикса
    """
    key = models.CharField(verbose_name='Ключ настройки', max_length=500)
    value = models.CharField(verbose_name='Значение настройки', max_length=500)

    def __str__(self):
        return self.value

    class Meta:
        ordering = ['-id']
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'


class Scrums(models.Model):
    """
    Модель для хранения инфы о скрамах.
    В основном используется для хранения информации об ID скрама в облаке битрикса и ID этого же скрама в коробке.
    Дополнительно указаны и другие поля.
    """
    scrum_cloud_id = models.CharField(verbose_name='ID скрама в облаке', max_length=20)
    scrum_box_id = models.CharField(verbose_name='ID скрама в коробке', max_length=20)
    scrum_title = models.CharField(verbose_name='Название скрама', max_length=200)
    scrum_master_id_cloud = models.CharField(verbose_name='ID скрам-мастера в облаке', max_length=100,
                                             blank=True, null=False)
    scrum_master_id_box = models.CharField(verbose_name='ID скрам-мастера в коробке', max_length=100,
                                           blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Скрам'
        verbose_name_plural = 'Скрамы'


class BitrixUsers(models.Model):
    """
    Модель для хранения инфы о пользователях битрикса.
    Опять же, модель нужна по большей части для связки пользователей коробки и облака.
    """
    user_id_cloud = models.CharField(verbose_name='ID юзера облака', max_length=20)
    user_id_box = models.CharField(verbose_name='ID юзера коробки', max_length=20)
    email = models.CharField(verbose_name='EMAIL', max_length=100)
    name = models.CharField(verbose_name='Имя', max_length=100)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Юзер битрикса'
        verbose_name_plural = 'Юзеры битрикса'


class Backlog(models.Model):
    """
    Модель для бэклогов.
    """
    backlog_id_cloud = models.CharField(verbose_name='ID Бэклога облака', max_length=20)
    backlog_id_box = models.CharField(verbose_name='ID Бэклога коробки', max_length=20)
    scrum_cloud_id = models.CharField(verbose_name='ID скрама в облаке', max_length=20)
    scrum_box_id = models.CharField(verbose_name='ID скрама в коробке', max_length=20)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Бэклог'
        verbose_name_plural = 'Бэклоги'


class Sprint(models.Model):
    """
    Модель для спринтов.
    """
    sprint_id_cloud = models.CharField(verbose_name='ID спринта в облаке', max_length=20)
    sprint_id_box = models.CharField(verbose_name='ID спринта в коробке', max_length=20)
    scrum_cloud_id = models.CharField(verbose_name='ID скрама в облаке', max_length=20)
    scrum_box_id = models.CharField(verbose_name='ID скрама в коробке', max_length=20)
    sprint_name = models.CharField(verbose_name='Название спринта', max_length=200, blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Спринт'
        verbose_name_plural = 'Спринты'


class Epic(models.Model):
    """
    Модель для эпиков.
    """
    epic_id_cloud = models.CharField(verbose_name='ID эпика в облаке', max_length=20)
    epic_id_box = models.CharField(verbose_name='ID эпика в коробке', max_length=20)
    scrum_cloud_id = models.CharField(verbose_name='ID скрама в облаке', max_length=20)
    scrum_box_id = models.CharField(verbose_name='ID скрама в коробке', max_length=20)
    epic_name = models.CharField(verbose_name='Название эпика', max_length=200)
    epic_files = models.CharField(verbose_name='Файлы в эпике', max_length=350, blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Эпик'
        verbose_name_plural = 'Эпики'


class ScrumTask(models.Model):
    """
    Модель для задач скрама.
    """
    task_id_cloud = models.CharField(verbose_name='ID задачи в облаке', max_length=20)
    task_id_box = models.CharField(verbose_name='ID задачи в коробке', max_length=20)
    stage_id_cloud = models.CharField(verbose_name='ID стадии задачи в облаке', max_length=20, blank=True, null=False)
    stage_id_box = models.CharField(verbose_name='ID стадии задачи в коробке', max_length=20, blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class TaskComment(models.Model):
    """
    Модель для комментариев к задачам.
    """
    comment_id_cloud = models.CharField(verbose_name='ID коммента в облаке', max_length=20)
    comment_id_box = models.CharField(verbose_name='ID коммента в коробке', max_length=20)
    author_id_cloud = models.CharField(verbose_name='ID автора в облаке', max_length=20)
    author_id_box = models.CharField(verbose_name='ID автора в коробке', max_length=20)
    author_mail = models.CharField(verbose_name='EMAIL автора', max_length=100)
    files_in_comments = models.CharField(verbose_name='Файлы в комментарие', max_length=350, blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Комментарий задачи'
        verbose_name_plural = 'Комментарии задач'


class Kanban(models.Model):
    """
    Модель для канбанов спринта.
    """
    sprint_id_cloud = models.CharField(verbose_name='ID спринта в облаке', max_length=20, blank=True, null=False)
    sprint_id_box = models.CharField(verbose_name='ID спринта в коробке', max_length=20, blank=True, null=False)
    stages_id_cloud = models.CharField(verbose_name='ID стадий через пробел облако', max_length=250, blank=True, null=False)
    stages_id_box = models.CharField(verbose_name='ID стадий через пробел коробка', max_length=250, blank=True, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Канбан'
        verbose_name_plural = 'Канбан'
