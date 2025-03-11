from django.urls import path
from .views import verify_google_token
from . import views

urlpatterns = [
    path('api/verify-google-token/', verify_google_token, name='verify_google_token'),

]