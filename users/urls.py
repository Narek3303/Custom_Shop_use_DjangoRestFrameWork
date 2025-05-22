from django.urls import path
from .views import verify_google_token
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet

# Ստեղծում ենք router
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='userprofile')



urlpatterns = [
    path('api/verify-google-token/', verify_google_token, name='verify_google_token'),
    path('users/', include(router.urls)),  # Բոլոր viewset-ների համար ավտոմատ URL-ներ
    path('profile/me/', UserProfileViewSet.as_view({'get': 'me', 'put': 'me'}), name='profile-me'),
    path('profile/deactivate/', UserProfileViewSet.as_view({'post': 'deactivate'}), name='profile-deactivate'),
]
