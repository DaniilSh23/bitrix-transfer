from django.urls import path

from scrum_transfer.views import start_bitrix_cloud, common_bitrix_cloud, start_bitrix_box, common_bitrix_box, \
    TestBtrxMethod, ScrumTransferView, BacklogTransfer, SprintTransfer, EpicTransfer

urlpatterns = [
    path('start_bitrix_cloud/', start_bitrix_cloud, name='start_bitrix_cloud'),
    path('common_bitrix_cloud/', common_bitrix_cloud, name='common_bitrix_cloud'),
    path('start_bitrix_box/', start_bitrix_box, name='start_bitrix_box'),
    path('common_bitrix_box/', common_bitrix_box, name='common_bitrix_box'),
    path('scrum_transfer/', ScrumTransferView.as_view(), name='scrum_transfer'),    # Перенос скрамов и приглашения юзеров
    path('backlog_transfer/', BacklogTransfer.as_view(), name='backlog_transfer'),  # Перенос бэклогов для скрамов
    path('sprint_transfer/', SprintTransfer.as_view(), name='sprint_transfer'),     # Перенос спринтов для скрамов
    path('epic_transfer/', EpicTransfer.as_view(), name='epic_transfer'),   # Перенос эпиков для скрамов

    # Тестовый обработчик
    path('test/', TestBtrxMethod.as_view(), name='test'),
]
