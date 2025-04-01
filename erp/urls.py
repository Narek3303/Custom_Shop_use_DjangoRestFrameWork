from django.urls import path
from .api.views import ERPSyncView

urlpatterns = [
    path('sync/<int:integration_id>/', ERPSyncView.as_view(), name='erp-sync'),
]
