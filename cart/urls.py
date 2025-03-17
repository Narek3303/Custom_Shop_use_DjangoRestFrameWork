from django.urls import path
from . import views

urlpatterns = [
    # Զամբյուղի մանրամասների ստացում
    path('cart/', views.CartDetailAPIView.as_view(), name='cart-detail'),


    # Ապրանքի հեռացում զամբյուղից
    path('cart/remove/<int:product_id>/', views.CartRemoveAPIView.as_view(), name='cart-remove'),

    # Զամբյուղի մաքրում
    path('cart/clear/', views.CartClearAPIView.as_view(), name='cart-clear'),

    # Ապրանքի քանակի թարմացում
    path('cart/update/<int:product_id>/', views.CartUpdateAPIView.as_view(), name='cart-update'),

    # Զամբյուղի ընդհանուր գնի ստացում
    path('cart/total_price/', views.CartTotalPriceAPIView.as_view(), name='cart-total-price'),
    ]