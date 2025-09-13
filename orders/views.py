import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
from django.shortcuts import render
import requests
import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django_filters.rest_framework import DjangoFilterBackend
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.models import PayPalIPN
from rest_framework import status, permissions, viewsets, filters
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
# from django_weasyprint.views import WeasyTemplateResponseMixin

from shop.models import Product
from users.models import UserProfile
from cart.models import Cart
from .exceptions import (
    InventoryError,
    PaymentProcessingError,
    FraudDetectionError,
    OrderValidationError
)
from .filters import OrderFilter
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    AnalyticsSerializer,

)
from .tasks import send_order_status_email, send_sms
from .utils.pdf_generator import generate_invoice_pdf

# Initialize logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderStatus
from .serializers import OrderSerializer, OrderCreateSerializer


class OrderListView(generics.ListAPIView):
    """
    List of orders for authenticated user.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """
    Single order details for authenticated user.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


@csrf_exempt
def webmoney_result(request):
    if request.method == "POST":
        # Ստանում ենք WebMoney-ի տվյալները
        lmi_payment_no = request.POST.get('LMI_PAYMENT_NO')
        lmi_payment_amount = request.POST.get('LMI_PAYMENT_AMOUNT')
        lmi_payee_purse = request.POST.get('LMI_PAYEE_PURSE')
        lmi_sys_invs_no = request.POST.get('LMI_SYS_INVS_NO')
        lmi_sys_trans_no = request.POST.get('LMI_SYS_TRANS_NO')
        lmi_sys_trans_date = request.POST.get('LMI_SYS_TRANS_DATE')
        lmi_secret_key = 'your_secret_key'  # Փոխարինեք ձեր գաղտնաբառով

        # Ստուգում ենք hash-ը
        hash_str = f"{lmi_payment_no}{lmi_payment_amount}{lmi_payee_purse}{lmi_sys_invs_no}{lmi_sys_trans_no}{lmi_sys_trans_date}{lmi_secret_key}"
        calculated_hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest().upper()

        if calculated_hash == request.POST.get('LMI_HASH'):
            try:
                order = Order.objects.get(id=lmi_payment_no)
                if float(lmi_payment_amount) == float(order.total):
                    order.is_paid = True
                    order.payment_id = lmi_sys_trans_no
                    order.save()
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Amount mismatch'}, status=400)
            except Order.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid hash'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def payment_success(request):
    return render(request, 'payment_success.html', {
        'message': 'Վճարումը հաջողությամբ կատարվել է։ Շնորհակալություն գնումների համար։'
    })


def payment_fail(request):
    return render(request, 'payment_fail.html', {
        'message': 'Վճարումը չի կատարվել։ Խնդրում ենք փորձել կրկին։'
    })

class OrderCreateView(generics.CreateAPIView):
    """
    Create an order from client-provided data (e.g. from frontend checkout).
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]  # Or use custom permission

    def perform_create(self, serializer):
        serializer.save()


class OrderStatusUpdateView(APIView):
    """
    Admin or staff can change order status.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in dict(OrderStatus.choices):
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save(update_fields=["status"])
        return Response({"detail": "Status updated."})


def check_inventory(view_func):
    """Decorator to check product inventory before processing orders."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            items = request.data.get('items', [])
            for item in items:
                product = get_object_or_404(Product, id=item['product_id'])
                if product.inventory_count < item['quantity']:
                    raise InventoryError(
                        f"Insufficient inventory for {product.name}"
                    )
            return view_func(request, *args, **kwargs)

        except InventoryError as e:
            logger.warning("Inventory check failed: %s", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    return wrapper


class OrderAnalyticsView(APIView):
    """Provides comprehensive analytics for orders with time-based filtering."""
    permission_classes = [IsAdminUser]

    ANALYTICS_PERIODS = {
        'day': timedelta(days=1),
        'week': timedelta(weeks=1),
        'month': timedelta(days=30),
        'year': timedelta(days=365),
        'default': timedelta(days=7)
    }

    def get(self, request):
        """Returns analytics data for the specified time period."""
        try:
            date_range = self._get_date_range(request)
            analytics_data = self._generate_analytics(date_range)

            serializer = AnalyticsSerializer(analytics_data)
            return Response(serializer.data)

        except Exception as e:
            logger.error("Analytics generation error: %s", str(e))
            return Response(
                {"error": "Error generating analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_date_range(self, request):
        """Determines the date range for analytics based on request parameters."""
        period = request.query_params.get('period', 'week')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')

        if date_from and date_to:
            return (date_from, date_to)

        time_delta = self.ANALYTICS_PERIODS.get(period, self.ANALYTICS_PERIODS['default'])
        return (datetime.now() - time_delta, datetime.now())

    def _generate_analytics(self, date_range):
        """Generates all analytics data for the given date range."""
        return {
            'sales_over_time': self._get_sales_over_time(date_range),
            'top_products': self._get_top_products(date_range),
            'revenue_stats': self._get_revenue_stats(date_range),
            'order_status_stats': self._get_order_status_stats(date_range),
            'payment_method_stats': self._get_payment_method_stats(date_range),
        }

    def _get_sales_over_time(self, date_range):
        """Gets sales data aggregated by time period."""
        date_from, date_to = date_range
        orders = Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status__in=['paid', 'completed']
        )

        trunc_func = self._determine_truncation(date_from, date_to)

        return orders.annotate(
            date=trunc_func('created_at')
        ).values('date').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('date')

    def _determine_truncation(self, date_from, date_to):
        """Determines the appropriate time truncation for aggregation."""
        if isinstance(date_from, str) or isinstance(date_to, str):
            return TruncDate

        delta = date_to - date_from

        if delta.days > 365:
            return TruncYear
        elif delta.days > 30:
            return TruncMonth
        return TruncDate

    def _get_top_products(self, date_range, limit=5):
        """Gets the top selling products."""
        date_from, date_to = date_range

        return OrderItem.objects.filter(
            order__created_at__gte=date_from,
            order__created_at__lte=date_to,
            order__status__in=['paid', 'completed']
        ).values(
            'product__id',
            'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('-total_sold')[:limit]

    def _get_revenue_stats(self, date_range):
        """Calculates comprehensive revenue statistics."""
        date_from, date_to = date_range

        current_stats = Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status__in=['paid', 'completed']
        ).aggregate(
            total_revenue=Sum('total'),
            avg_order_value=ExpressionWrapper(
                Sum('total') / Count('id'),
                output_field=DecimalField()
            ),
            total_orders=Count('id')
        )

        current_stats['revenue_change_percent'] = self._calculate_revenue_change(
            date_from,
            date_to,
            current_stats.get('total_revenue', 0)
        )

        return current_stats

    def _calculate_revenue_change(self, date_from, date_to, current_revenue):
        """Calculates revenue change compared to previous period."""
        prev_period_length = date_to - date_from
        prev_date_from = date_from - prev_period_length

        prev_revenue = Order.objects.filter(
            created_at__gte=prev_date_from,
            created_at__lte=date_from,
            status__in=['paid', 'completed']
        ).aggregate(
            total_revenue=Sum('total')
        ).get('total_revenue', 0) or 0

        current_revenue = current_revenue or 0

        if prev_revenue > 0:
            return round(((current_revenue - prev_revenue) / prev_revenue) * 100, 2)
        return 100 if current_revenue > 0 else 0

    def _get_order_status_stats(self, date_range):
        """Gets statistics on order statuses."""
        date_from, date_to = date_range

        return Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to
        ).values('status').annotate(
            count=Count('id')
        ).order_by('-count')

    def _get_payment_method_stats(self, date_range):
        """Gets statistics on payment methods."""
        date_from, date_to = date_range

        return Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status__in=['paid', 'completed']
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')


# class OrderPDFView(WeasyTemplateResponseMixin, DetailView):
#     """Generates PDF invoices for orders with company branding."""
#     model = Order
#     template_name = 'orders/invoice_pdf.html'
#     pdf_filename = 'invoice.pdf'
#     pdf_attachment = True
#
#     def get_context_data(self, **kwargs):
#         """Enriches the template context with order and company data."""
#         context = super().get_context_data(**kwargs)
#         order = self.object
#
#         context.update({
#             'order': order,
#             'items': order.items.all().select_related('product'),
#             'company': self._get_company_info(),
#             'dates': self._get_invoice_dates(),
#             'shipping': getattr(order, 'shipping', None)
#         })
#
#         return context
#
#     def _get_company_info(self):
#         """Retrieves company information from settings."""
#         return {
#             'name': settings.COMPANY_NAME,
#             'address': settings.COMPANY_ADDRESS,
#             'phone': settings.COMPANY_PHONE,
#             'email': settings.COMPANY_EMAIL,
#             'tax_id': settings.COMPANY_TAX_ID,
#             'logo': settings.COMPANY_LOGO_URL
#         }
#
#     def _get_invoice_dates(self):
#         """Generates dates for the invoice."""
#         return {
#             'today': datetime.now().strftime("%B %d, %Y"),
#             'due_date': (datetime.now() + timedelta(days=14)).strftime("%B %d, %Y")
#         }


def download_invoice(request, order_id):
    """Downloads an invoice PDF for a specific order."""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        pdf_bytes, invoice = generate_invoice_pdf(order, save_to_file=True)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response

    except Exception as e:
        logger.error("Invoice download error for order %s: %s", order_id, str(e))
        return HttpResponse(
            "Error generating invoice",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

