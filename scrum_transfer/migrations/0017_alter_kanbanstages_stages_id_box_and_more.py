# Generated by Django 4.1.7 on 2023-03-24 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrum_transfer', '0016_alter_kanbanstages_options_alter_scrums_scrum_box_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kanbanstages',
            name='stages_id_box',
            field=models.CharField(blank=True, max_length=250, verbose_name='ID стадии коробка'),
        ),
        migrations.AlterField(
            model_name='kanbanstages',
            name='stages_id_cloud',
            field=models.CharField(blank=True, max_length=250, verbose_name='ID стадии облако'),
        ),
    ]
