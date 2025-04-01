from django.urls import path, include
from rest_framework.routers import DefaultRouter
from security.api.views import AllowedIPViewSet, BlockedIPViewSet

# Ստեղծում ենք router
router = DefaultRouter()
router.register(r'allowed-ips', AllowedIPViewSet, basename='allowed-ip')
router.register(r'blocked-ips', BlockedIPViewSet, basename='blocked-ip')

urlpatterns = [
    path('', include(router.urls)),  # API-ի համար ավելացնում ենք router-ի URL-ները
]