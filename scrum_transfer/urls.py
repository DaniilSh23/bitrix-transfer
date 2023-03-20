from django.urls import path

from scrum_transfer.views import start_bitrix_cloud, common_bitrix_cloud, start_bitrix_box, common_bitrix_box, \
    TestBtrxMethod, ScrumTransferView

urlpatterns = [
    path('start_bitrix_cloud/', start_bitrix_cloud, name='start_bitrix_cloud'),
    path('common_bitrix_cloud/', common_bitrix_cloud, name='common_bitrix_cloud'),
    path('start_bitrix_box/', start_bitrix_box, name='start_bitrix_box'),
    path('common_bitrix_box/', common_bitrix_box, name='common_bitrix_box'),
    path('scrum_transfer/', ScrumTransferView.as_view(), name='scrum_transfer'),

    # Тестовый обработчик
    path('test/', TestBtrxMethod.as_view(), name='test'),
]
