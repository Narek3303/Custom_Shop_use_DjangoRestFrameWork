import uuid

import requests
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
import logging
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, ShippingSerializer, ShippingMethodSerializer
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ValidationError
from django.db import transaction
from paypal.standard.forms import PayPalPaymentsForm
from rest_framework.views import APIView
from django.conf import settings
import stripe
from paypal.standard.ipn.models import PayPalIPN
from .tasks import send_order_status_email, send_sms
from .filters import OrderFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from decimal import Decimal, InvalidOperation
from rest_framework import status, permissions
from shop.models import Product
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from datetime import datetime, timedelta, timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from .models import Order, OrderItem, ShippingMethod, Shipping, ShippingAddress
from .serializers import AnalyticsSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Order, Invoice
from .utils.pdf_generator import generate_invoice_pdf
from django_weasyprint.views import WeasyTemplateResponseMixin
from django.views.generic import DetailView




logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows orders to be viewed, created, and updated.
    """
    queryset = Order.objects.all().prefetch_related("items")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'status']
    search_fields = ['order_id', 'customer__email']

    def get_queryset(self):
        """
        Restrict orders to the logged-in user unless they are staff.
        """
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Assign the logged-in user to the order and recalculate total.
        """
        order = serializer.save(user=self.request.user)
        order.total = order.calculate_total()
        order.save()

    @action(detail=True, methods=["patch"], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """
        Update the status of an order. Only accessible by admin users.
        """
        # Step 1: Retrieve the order or return 404 if not found
        order = self.get_object()

        # Step 2: Extract and validate the status value from the request
        try:
            status_value = self.get_status_from_request(request)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Validate if the status value is valid
        if not self.is_valid_status(status_value):
            valid_statuses = ', '.join(self.get_valid_statuses().keys())
            return Response({
                "error": f"Invalid status. Valid statuses are: {valid_statuses}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 4: Check if the new status is different from the current one
        if order.status == status_value:
            return Response({
                "error": "The order is already in the specified status."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 5: Update the order status safely with an atomic transaction
        try:
            with transaction.atomic():
                # Ensure that changes are done atomically
                order.status = status_value
                order.save()
                logger.info(f"Order {order.id} status successfully updated to {status_value}.")

            # Send Celery tasks to handle notifications
            send_order_status_email.delay(order.id)  # Asynchronous email task
            send_sms.delay(order.id)  # Asynchronous SMS task

            # Return success response
            return Response({
                "message": f"Order status successfully updated to {status_value}."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error occurred while updating order {order.id}: {str(e)}")
            return Response({"error": f"An unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)




    def get_order(self, pk):
        """
        Helper method to retrieve an order by pk or raise 404.
        """
        return get_object_or_404(Order, pk=pk)

    def get_status_from_request(self, request):
        """
        Helper method to retrieve 'status' from the request data.
        """
        status_value = request.data.get("status")
        if not status_value:
            raise ValidationError("Status is required.")
        return status_value.strip()  # Ensure we don't have any leading/trailing spaces

    def is_valid_status(self, status_value):
        """
        Validate if the provided status is within the valid choices.
        """
        return status_value in self.get_valid_statuses()

    def get_valid_statuses(self):
        """
        Returns the dictionary of valid statuses for an order.
        """
        return dict(Order.Status.choices)  # Assuming Order has a Status model with valid choices

    @action(detail=True, methods=["get"])
    def calculate_total(self, request, pk=None):
        """
        Recalculate the total cost of an order.
        """
        order = get_object_or_404(Order, pk=pk)
        order.total = order.calculate_total()
        order.save()
        return Response({"total": order.total}, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing order items.
    """
    queryset = OrderItem.objects.all().select_related("order", "product")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Ensure the order total is updated when an item is added.
        """
        order_item = serializer.save()
        order = order_item.order
        order.total = order.calculate_total()
        order.save()


class CreatePaymentView(APIView):
    """ Ստեղծում է PayPal վճարման հարցում """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")

        # Ստուգում ենք, որ order_id-ն կա
        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Ստուգում ենք՝ արդյոք պատվերը առկա է
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Ստուգում ենք, որ պատվերը դեռ չի վճարվել
        if order.status == "Paid":
            return Response({"error": "This order is already paid"}, status=status.HTTP_400_BAD_REQUEST)

        # PayPal API-ի կարգավորումներ
        paypal_dict = {
            "business": settings.PAYPAL_RECEIVER_EMAIL,
            "amount": str(order.total_amount.quantize(Decimal("0.01"))),
            "item_name": f"Order {order.id}",
            "invoice": str(order.id),
            "currency_code": settings.PAYPAL_CURRENCY,
            "notify_url": settings.PAYPAL_NOTIFY_URL,
            "return_url": settings.PAYPAL_RETURN_URL,
            "cancel_return": settings.PAYPAL_CANCEL_URL,
        }

        form = PayPalPaymentsForm(initial=paypal_dict)
        return Response({"paypal_form": form.render()}, status=status.HTTP_200_OK)


class PayPalIPNView(APIView):
    """ Վերամշակում է PayPal-ից եկող IPN ծանուցումները """

    permission_classes = [permissions.AllowAny]  # PayPal IPN պետք է հասանելի լինի

    def post(self, request, *args, **kwargs):
        raw_post_data = request.body.decode("utf-8")

        # Վավերացման URL-ը PayPal-ի համար
        paypal_verify_url = "https://ipnpb.paypal.com/cgi-bin/webscr" if settings.PAYPAL_LIVE else "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"

        # Վավերացում IPN-ի համար
        verify_response = requests.post(paypal_verify_url, data={"cmd": "_notify-validate", **request.POST.dict()})

        # Ստուգում ենք՝ արդյոք վավեր է
        if verify_response.text != "VERIFIED":
            logger.warning("PayPal IPN verification failed")
            return Response({"error": "Invalid PayPal IPN"}, status=status.HTTP_400_BAD_REQUEST)

        txn_id = request.data.get("txn_id")
        invoice_id = request.data.get("invoice")
        payment_status = request.data.get("payment_status")
        mc_gross = request.data.get("mc_gross")

        # Ստուգում ենք՝ արդյոք բոլորը կարևորված տվյալները կան
        if not txn_id or not invoice_id or not payment_status or not mc_gross:
            logger.warning("Missing essential IPN data")
            return Response({"error": "Invalid IPN data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ստեղծում ենք պատվերի օբյեկտը
            order = get_object_or_404(Order, id=invoice_id)

            # Ստուգում ենք՝ արդյոք վճարումն արդեն կատարված է
            if order.status == "Paid":
                logger.info(f"Order {order.id} is already paid.")
                return Response({"message": "Order already processed"}, status=status.HTTP_200_OK)

            # Ստուգում ենք, որ վճարումը ճիշտ է
            if payment_status == "Completed" and Decimal(mc_gross) == order.total_amount:
                order.status = "Paid"
                order.save()

                logger.info(f"Payment successful for Order {order.id} - Transaction ID: {txn_id}")
                return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)

            logger.warning(f"Payment not completed for Order {order.id} - Status: {payment_status}")
            return Response({"error": "Payment not completed or amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error processing PayPal IPN: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateStripeCheckoutSession(APIView):
    """ Ստեղծում է Stripe Checkout Session անվտանգ, օպտիմալ և ֆունկցիոնալ """

    permission_classes = [permissions.IsAuthenticated]  # Միայն մուտք գործած օգտատերերը կարող են վճարում կատարել

    def post(self, request, *args, **kwargs):
        YOUR_DOMAIN = settings.FRONTEND_URL  # Ավելի ապահով և կարգավորվող բազային URL

        # Ստանում ենք օգտատիրոջ կողմից ուղարկված տվյալները
        items = request.data.get("items")  # Ակնկալում ենք [{"product_name": "Item1", "amount": 10, "quantity": 2}, ...]
        currency = request.data.get("currency", "usd").lower()  # Անհրաժեշտության դեպքում ավելացնել տարբեր արժույթներ

        if not items or not isinstance(items, list):
            raise ValidationError({"items": "A valid list of items is required."})

        line_items = []
        total_amount = Decimal(0)  # Ընդհանուր գումարի հաշվարկ

        for item in items:
            product_name = item.get("product_name", "Product")
            amount = item.get("amount")
            quantity = item.get("quantity", 1)

            if not amount:
                raise ValidationError({"amount": "Each item must have an amount."})

            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValidationError({"amount": "Amount must be greater than zero."})
            except (ValueError, TypeError, InvalidOperation):
                raise ValidationError({"amount": "Invalid amount format."})

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValidationError({"quantity": "Quantity must be greater than zero."})
            except (ValueError, TypeError):
                raise ValidationError({"quantity": "Invalid quantity format."})

            # Գումարը վերածում ենք ցենտերի (100x)
            unit_amount = int(amount * 100)
            total_amount += amount * quantity

            line_items.append({
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": product_name},
                    "unit_amount": unit_amount,
                },
                "quantity": quantity,
            })

        if total_amount <= 0:
            raise ValidationError({"total_amount": "Total payment amount must be greater than zero."})

        order_id = str(uuid.uuid4())  # Ունիվերսալ եզակի Order ID (UUID)

        try:
            # Ստեղծում ենք Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=f"{YOUR_DOMAIN}/payment/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{YOUR_DOMAIN}/payment/cancel/",
                metadata={"user_id": str(request.user.id), "order_id": order_id, "total_amount": str(total_amount)},
            )

            # Լոգավորում ենք պատվերը
            logger.info(f"Checkout session created: User {request.user.id} | Order {order_id} | Amount {total_amount}")

            return Response({"checkout_url": checkout_session.url, "order_id": order_id}, status=status.HTTP_200_OK)

        except stripe.error.CardError as e:
            logger.error(f"Card error for user {request.user.id}: {str(e)}")
            return Response({"error": f"Card error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.RateLimitError:
            logger.error(f"Rate limit error for user {request.user.id}")
            return Response({"error": "Too many requests to Stripe."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except stripe.error.InvalidRequestError:
            logger.error(f"Invalid request error for user {request.user.id}")
            return Response({"error": "Invalid request to Stripe API."}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.AuthenticationError:
            logger.error(f"Authentication error for user {request.user.id}")
            return Response({"error": "Stripe authentication failed."}, status=status.HTTP_403_FORBIDDEN)
        except stripe.error.APIConnectionError:
            logger.error(f"API connection error for user {request.user.id}")
            return Response({"error": "Network error. Please try again."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error for user {request.user.id}: {str(e)}")
            return Response({"error": f"Payment processing error: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error for user {request.user.id}: {str(e)}")
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StripePaymentSuccessView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "Payment successful!"}, status=status.HTTP_200_OK)

class StripePaymentCancelView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "Payment canceled"}, status=status.HTTP_200_OK)


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session(session)

        return Response(status=200)


def check_inventory(view_func):
    def wrapper(request, *args, **kwargs):
        items = request.data.get('items', [])
        for item in items:
            product = get_object_or_404(Product, id=item['product_id'])
            if product.inventory_count < item['quantity']:
                return Response(
                    {'error': f'Պահեստում բավարար քանակ չկա {product.name}-ի համար'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return view_func(request, *args, **kwargs)
    return wrapper




class OrderAnalyticsView(APIView):
    """
    Վերլուծական տվյալների վերջնակետ՝ ադմինիստրատորների համար
    Ապահովում է՝
    - Վաճառքներ ըստ ժամանակահատվածի
    - Ամենահայտնի ապրանքներ
    - Եկամուտ և պատվերների քանակ
    - Չեղարկված պատվերներ
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        time_period = request.query_params.get('period', 'week')  # day, week, month, year
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')

        # Ստուգում ենք ժամանակային միջակայքը
        date_range = self._get_date_range(time_period, date_from, date_to)

        # Հիմնական վիճակագրություն
        analytics_data = {
            'sales_over_time': self._get_sales_over_time(date_range),
            'top_products': self._get_top_products(date_range),
            'revenue_stats': self._get_revenue_stats(date_range),
            'order_status_stats': self._get_order_status_stats(date_range),
            'payment_method_stats': self._get_payment_method_stats(date_range),
        }

        serializer = AnalyticsSerializer(analytics_data)
        return Response(serializer.data)

    def _get_date_range(self, period, date_from=None, date_to=None):
        """Վերադարձնում է ժամանակային միջակայքը"""
        now = datetime.now()

        if date_from and date_to:
            return (date_from, date_to)

        if period == 'day':
            return (now - timedelta(days=1), now)
        elif period == 'week':
            return (now - timedelta(weeks=1), now)
        elif period == 'month':
            return (now - timedelta(days=30), now)
        elif period == 'year':
            return (now - timedelta(days=365), now)
        else:
            return (now - timedelta(days=7), now)  # Լռությամբ՝ վերջին շաբաթ

    def _get_sales_over_time(self, date_range):
        """Վաճառքների դինամիկան ըստ ժամանակահատվածի"""
        date_from, date_to = date_range
        orders = Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status__in=['paid', 'completed']
        )

        # Խմբավորում ըստ օր/ամիս/տարի
        trunc_func = TruncDate('created_at')
        if (date_to - date_from).days > 365:
            trunc_func = TruncYear('created_at')
        elif (date_to - date_from).days > 30:
            trunc_func = TruncMonth('created_at')

        sales_data = orders.annotate(
            date=trunc_func
        ).values('date').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('date')

        return list(sales_data)

    def _get_top_products(self, date_range, limit=5):
        """Ամենավաճառվող ապրանքները"""
        date_from, date_to = date_range
        top_products = OrderItem.objects.filter(
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

        return list(top_products)

    def _get_revenue_stats(self, date_range):
        """Եկամուտի վիճակագրություն"""
        date_from, date_to = date_range
        stats = Order.objects.filter(
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

        # Հաշվարկել փոփոխությունը նախորդ ժամանակահատվածի համեմատ
        prev_date_from = date_from - (date_to - date_from)
        prev_stats = Order.objects.filter(
            created_at__gte=prev_date_from,
            created_at__lte=date_from,
            status__in=['paid', 'completed']
        ).aggregate(
            total_revenue=Sum('total')
        )

        prev_revenue = prev_stats['total_revenue'] or 0
        current_revenue = stats['total_revenue'] or 0

        if prev_revenue > 0:
            change_percent = ((current_revenue - prev_revenue) / prev_revenue) * 100
        else:
            change_percent = 100 if current_revenue > 0 else 0

        stats['revenue_change_percent'] = round(change_percent, 2)
        return stats

    def _get_order_status_stats(self, date_range):
        """Պատվերների կարգավիճակների վիճակագրություն"""
        date_from, date_to = date_range
        status_stats = Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to
        ).values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        return list(status_stats)

    def _get_payment_method_stats(self, date_range):
        """Վճարման մեթոդների վիճակագրություն"""
        date_from, date_to = date_range
        payment_stats = Order.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status__in=['paid', 'completed']
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')

        return list(payment_stats)






class ShippingViewSet(viewsets.ModelViewSet):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Shipping.objects.all()
        return Shipping.objects.filter(order__user=user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        shipping = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status with appropriate timestamps
        if new_status == 'shipped' and shipping.status != 'shipped':
            shipping.shipped_at = timezone.now()
        elif new_status == 'delivered' and shipping.status != 'delivered':
            shipping.delivered_at = timezone.now()

        shipping.status = new_status
        shipping.save()

        return Response(
            {'status': 'Status updated successfully'},
            status=status.HTTP_200_OK
        )


class ShippingMethodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    permission_classes = [IsAuthenticated]


class ShippingCalculatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShippingCalculatorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Կատարել առաքման արժեքի հաշվարկ
        # Այստեղ կարող եք ինտեգրել արտաքին API (FedEx, UPS, etc.)
        # Կամ օգտագործել ձեր սեփական հաշվարկային տրամաբանությունը

        calculated_price = self._calculate_shipping(
            serializer.validated_data['country'],
            serializer.validated_data['city'],
            serializer.validated_data['weight'],
            serializer.validated_data['dimensions']
        )

        available_methods = ShippingMethod.objects.filter(is_active=True)
        methods_data = ShippingMethodSerializer(available_methods, many=True).data

        return Response({
            'calculated_price': calculated_price,
            'available_methods': methods_data
        })

    def _calculate_shipping(self, country, city, weight, dimensions):
        # Հիմնական հաշվարկային տրամաբանություն
        base_price = Decimal('10.00')  # Հիմնական արժեք

        # Ավելացնել զանգվածից կախված հավելավճար
        if weight > 5:  # կգ
            base_price += Decimal(weight - 5) * Decimal('0.5')

        # Երկրի հատուկ գործոններ
        if country == 'AM':  # Հայաստան
            return base_price
        elif country == 'US':
            return base_price * Decimal('1.5')
        elif country == 'RU':
            return base_price * Decimal('1.2')

        return base_price * Decimal('1.3')  # Այլ երկրների համար





class OrderPDFView(WeasyTemplateResponseMixin, DetailView):
    model = Order
    template_name = 'orders/invoice_pdf.html'
    pdf_filename = 'invoice.pdf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context.update({
            'order': order,
            'items': order.items.all(),
            'company': {
                'name': settings.COMPANY_NAME,
                'address': settings.COMPANY_ADDRESS,
                'phone': settings.COMPANY_PHONE,
                'email': settings.COMPANY_EMAIL,
                'tax_id': settings.COMPANY_TAX_ID,
                'logo': settings.COMPANY_LOGO_URL
            },
            'today': datetime.now().strftime("%B %d, %Y"),
            'due_date': (datetime.now() + timedelta(days=14)).strftime("%B %d, %Y")
        })
        return context


def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    pdf_bytes, invoice = generate_invoice_pdf(order, save_to_file=True)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    return response