# Generated by Django 4.1.7 on 2023-03-23 16:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scrum_transfer', '0014_alter_taskcomment_files_in_comments'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Kanban',
            new_name='KanbanStages',
        ),
    ]
