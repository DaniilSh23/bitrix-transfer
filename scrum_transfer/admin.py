from django.contrib import admin
from scrum_transfer.models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    list_display_links = ['key', 'value']
