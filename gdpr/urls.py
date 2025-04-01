from django.urls import path
from .views import (
    GDPRConsentView,
    DataPortabilityAPIView,
    RightToBeForgottenAPIView,
    GDPRAdminAPIView,
)

urlpatterns = [
    # Frontend Views (HTML)
    path('consent/', GDPRConsentView.as_view(), name='gdpr-consent'),

    # API Endpoints
    path('api/data-export/', DataPortabilityAPIView.as_view(), name='data-portability'),
    path('api/request-erasure/', RightToBeForgottenAPIView.as_view(), name='right-to-be-forgotten'),

    # Admin Tools
    path('admin/requests/', GDPRAdminAPIView.as_view(), name='gdpr-admin-requests'),
    path('admin/requests/<uuid:request_id>/', GDPRAdminAPIView.as_view(), name='gdpr-admin-request-detail'),
]