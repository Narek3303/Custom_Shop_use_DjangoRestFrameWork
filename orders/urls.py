from django.urls import path
from .views import (

    OrderAnalyticsView,
    # OrderPDFView,
    download_invoice,
    OrderListView, OrderDetailView, OrderCreateView, OrderStatusUpdateView

)
from . import views

urlpatterns = [
    path('analytics/', OrderAnalyticsView.as_view(), name='order-analytics'),
    path('analytics/<str:period>/', OrderAnalyticsView.as_view(), name='order-analytics-period'),
    # path('order/<int:pk>/pdf/', OrderPDFView.as_view(), name='order-pdf'),
    path('order/<int:order_id>/download-invoice/', download_invoice, name='download-invoice'),

    path('', OrderListView.as_view(), name='order-list'),
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),

    path('payment/webmoney/result/', views.webmoney_result, name='webmoney_result'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),

]


