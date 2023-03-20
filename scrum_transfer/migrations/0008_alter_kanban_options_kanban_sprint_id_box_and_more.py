# Generated by Django 4.1.7 on 2023-03-20 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrum_transfer', '0007_kanban_epic_epic_files_scrumtask_stage_id_box_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kanban',
            options={'ordering': ['-id'], 'verbose_name': 'Канбан', 'verbose_name_plural': 'Канбан'},
        ),
        migrations.AddField(
            model_name='kanban',
            name='sprint_id_box',
            field=models.CharField(blank=True, max_length=20, verbose_name='ID спринта в коробке'),
        ),
        migrations.AddField(
            model_name='kanban',
            name='sprint_id_cloud',
            field=models.CharField(blank=True, max_length=20, verbose_name='ID спринта в облаке'),
        ),
        migrations.AddField(
            model_name='kanban',
            name='stages_id_box',
            field=models.CharField(blank=True, max_length=250, verbose_name='ID стадий через пробел коробка'),
        ),
        migrations.AddField(
            model_name='kanban',
            name='stages_id_cloud',
            field=models.CharField(blank=True, max_length=250, verbose_name='ID стадий через пробел облако'),
        ),
    ]