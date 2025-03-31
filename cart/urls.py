from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartListView.as_view(), name='cart-list'),
    path('add/', views.AddToCartView.as_view(), name='add-to-cart'),
    path('remove/', views.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('cart/update-quantity/', views.UpdateCartItemQuantityView.as_view(), name='update-cart-item'),
    path('clear/', views.ClearCartView.as_view(), name='clear-cart'),
    path('close/', views.CloseCartView.as_view(), name='close-cart'),
]
