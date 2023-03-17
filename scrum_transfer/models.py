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
