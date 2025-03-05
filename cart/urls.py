from django.urls import path
from .views import CartAddAPIView, CartRemoveAPIView, CartDetailAPIView

urlpatterns = [
    path('add/<int:product_id>/', CartAddAPIView.as_view(), name='cart-add'),
    path('remove/<int:product_id>/', CartRemoveAPIView.as_view(), name='cart-remove'),
    path('detail/', CartDetailAPIView.as_view(), name='cart-detail'),
]