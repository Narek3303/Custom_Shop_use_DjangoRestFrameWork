from django.urls import path
from . import views
from rest_framework.routers import SimpleRouter

# router = SimpleRouter()
# router.register('users', views.UserViewSet, base_name='users')
# router.register('', views.PostViewSet, base_name='posts')


urlpatterns = [
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('', views.PostListAPIView.as_view(), name='post_list'),
    path('<int:pk>/', views.PostDetailAPIView.as_view(), name='post_detail'),
]


# urlpatterns = router.urls