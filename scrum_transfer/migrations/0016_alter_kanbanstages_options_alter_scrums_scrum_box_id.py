# Generated by Django 4.1.7 on 2023-03-24 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrum_transfer', '0015_rename_kanban_kanbanstages'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kanbanstages',
            options={'ordering': ['-id'], 'verbose_name': 'Стадия канбана', 'verbose_name_plural': 'Стадии канбана'},
        ),
        migrations.AlterField(
            model_name='scrums',
            name='scrum_box_id',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='ID скрама в коробке'),
        ),
    ]
