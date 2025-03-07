from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartDetailAPIView.as_view(), name='cart_detail'),  # Get all cart details
    path('add/<int:product_id>/', views.CartAddAPIView.as_view(), name='cart_add'),  # Add item to cart
    path('remove/<int:product_id>/', views.CartRemoveAPIView.as_view(), name='cart_remove'),  # Remove item from cart
    path('clear/', views.CartClearAPIView.as_view(), name='cart_clear'),  # Clear the cart
    path('update/<int:product_id>/', views.CartUpdateAPIView.as_view(), name='cart_update'),  # Update quantity of item
    path('total_price/', views.CartTotalPriceAPIView.as_view(), name='cart_total_price'),  # Get total price of cart
]