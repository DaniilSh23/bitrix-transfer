from django.contrib import admin
from scrum_transfer.models import Settings, KanbanStages, TaskComment, ScrumTask, Epic, Sprint, Backlog, BitrixUsers, Scrums


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    list_display_links = ['key', 'value']


@admin.register(Scrums)
class ScrumsAdmin(admin.ModelAdmin):
    list_display = [
        'scrum_cloud_id',
        'scrum_box_id',
        'scrum_title',
        'scrum_master_id_cloud',
        'scrum_master_id_box',
        'is_archived',
    ]
    list_display_links = [
        'scrum_cloud_id',
        'scrum_box_id',
        'scrum_title',
        'scrum_master_id_cloud',
        'scrum_master_id_box',
    ]
    search_fields = [
        'scrum_cloud_id',
        'scrum_box_id',
        'scrum_title',
        'scrum_master_id_cloud',
        'scrum_master_id_box',
    ]
    search_help_text = 'Поиск по всем полям в таблице'
    list_editable = ['is_archived']


@admin.register(BitrixUsers)
class BitrixUsersAdmin(admin.ModelAdmin):
    list_display = [
        'user_id_cloud',
        'user_id_box',
        'email',
        'name',
    ]
    list_display_links = [
        'user_id_cloud',
        'user_id_box',
        'email',
        'name',
    ]
    search_fields = [
        'user_id_cloud',
        'user_id_box',
        'email',
        'name',
    ]
    search_help_text = 'Поиск по всем полям таблицы'


@admin.register(Backlog)
class BacklogAdmin(admin.ModelAdmin):
    list_display = [
        'backlog_id_cloud',
        'backlog_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
    ]
    list_display_links = [
        'backlog_id_cloud',
        'backlog_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
    ]
    list_filter = [
        'scrum_cloud_id',
        'scrum_box_id',
    ]


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = [
        'sprint_id_cloud',
        'sprint_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'sprint_name',
    ]
    list_display_links = [
        'sprint_id_cloud',
        'sprint_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'sprint_name',
    ]
    list_filter = [
        'scrum_cloud_id',
        'scrum_box_id',
        'sprint_name',
    ]


@admin.register(Epic)
class EpicAdmin(admin.ModelAdmin):
    list_display = [
        'epic_id_cloud',
        'epic_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'epic_name',
        'epic_files',
    ]
    list_display_links = [
        'epic_id_cloud',
        'epic_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'epic_name',
        'epic_files',
    ]
    list_filter = [
        'scrum_cloud_id',
        'scrum_box_id',
    ]


@admin.register(ScrumTask)
class ScrumTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_id_cloud',
        'task_id_box',
        'stage_id_cloud',
        'stage_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'comments_count',
    ]
    list_display_links = [
        'task_id_cloud',
        'task_id_box',
        'stage_id_cloud',
        'stage_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
        'comments_count',
    ]
    list_filter = [
        'stage_id_cloud',
        'stage_id_box',
        'scrum_cloud_id',
        'scrum_box_id',
    ]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = [
        'comment_id_cloud',
        'comment_id_box',
        'author_id_cloud',
        'author_id_box',
        'author_mail',
        'files_in_comments',
    ]
    list_display_links = [
        'comment_id_cloud',
        'comment_id_box',
        'author_id_cloud',
        'author_id_box',
        'author_mail',
        'files_in_comments',
    ]
    list_filter = [
        'author_id_cloud',
        'author_id_box',
        'author_mail',
    ]


@admin.register(KanbanStages)
class KanbanAdmin(admin.ModelAdmin):
    list_display = [
        'sprint_id_cloud',
        'sprint_id_box',
        'stages_id_cloud',
        'stages_id_box',
    ]
    list_display_links = [
        'sprint_id_cloud',
        'sprint_id_box',
        'stages_id_cloud',
        'stages_id_box',
    ]
    list_filter = [
        'sprint_id_cloud',
        'sprint_id_box',
    ]