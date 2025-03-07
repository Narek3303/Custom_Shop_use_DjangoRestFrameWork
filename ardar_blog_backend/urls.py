from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.schemas import get_schema_view


schema_view = get_schema_view(title='Blog API')


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include('post.urls')),
    # path('api-auth/', include('rest_framework.urls')),
    # path('api/rest-auth/', include('dj_rest_auth.urls')),
    # path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('schema/', schema_view),
    # path('auth/social/', include('allauth.socialaccount.urls')),
    # path('accounts/', include('allauth.urls')),
    path('api/accounts/', include('authemail.urls')),
    path("api/accounts/auth/", include("social_django.urls", namespace="social")),
    path('api/accounts/auth/', include('drf_social_oauth2.urls', namespace='drf')),
    # path('accounts/', include('allauth.urls')),
    path('shop/', include('shop.urls')),
    # path('cart/', include('cart.urls')),





]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



