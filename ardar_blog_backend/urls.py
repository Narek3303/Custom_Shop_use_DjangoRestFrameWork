from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.schemas import get_schema_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



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
    path('cart/', include('cart.urls')),
    path('coupon/', include('coupon.urls')),
    path('gdpr/', include('gdpr.urls')),
    path('orders/', include('orders.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('erp/', include('erp.urls')),
    path('security/', include('security.urls')),
    path('users/', include('users.urls')),







] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    # serve static files from STATICFILES_DIRS & app static dirs
    urlpatterns += staticfiles_urlpatterns()
    # serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production: ստատիկ ֆայլերը սպասարկում է web server–ը կամ Whitenoise
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



