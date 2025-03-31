from django.urls import path
from .views import (
    OrderViewSet,
    OrderItemViewSet,
    CreatePaymentView,
    PayPalIPNView,
    CreateStripeCheckoutSession,
    StripeWebhookView,
    StripePaymentSuccessView,
    StripePaymentCancelView,
    OrderAnalyticsView,
    ShippingViewSet,
    ShippingMethodViewSet,
    ShippingCalculatorView,
    OrderPDFView,
    download_invoice

)

urlpatterns = [
    # Վճարման վերջնակետեր
    path('paypal/create-payment/', CreatePaymentView.as_view(), name='paypal-create-payment'),
    path('paypal/ipn/', PayPalIPNView.as_view(), name='paypal-ipn'),

    path('stripe/create-checkout-session/', CreateStripeCheckoutSession.as_view(), name='stripe-create-session'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('stripe/success/', StripePaymentSuccessView.as_view(), name='stripe-success'),
    path('stripe/cancel/', StripePaymentCancelView.as_view(), name='stripe-cancel'),

    # Վերլուծական վերջնակետեր
    path('analytics/', OrderAnalyticsView.as_view(), name='order-analytics'),
    path('analytics/<str:period>/', OrderAnalyticsView.as_view(), name='order-analytics-period'),
    path('shipping/calculate/', ShippingCalculatorView.as_view(), name='shipping-calculate'),
    path('order/<int:pk>/pdf/', OrderPDFView.as_view(), name='order-pdf'),
    path('order/<int:order_id>/download-invoice/', download_invoice, name='download-invoice'),


    # DRF ViewSet-ների URL-ներ (Router-ի միջոցով)
]

# Եթե օգտագործում եք DRF-ի Router
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')
router.register(r'shippings', ShippingViewSet, basename='shipping')
router.register(r'shipping-methods', ShippingMethodViewSet, basename='shipping-method')

urlpatterns += router.urls
