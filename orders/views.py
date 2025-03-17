import weasyprint
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.contrib import messages

from cart.cart import Cart

from .models import Order, OrderItem



from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer
from .tasks import send_order_confirmation_email


class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: Retrieve a list of orders.
    POST: Create a new order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can create or view orders.

    def perform_create(self, serializer):
        # Create order and send confirmation email asynchronously
        order = serializer.save()
        send_order_confirmation_email.delay(order.id)


class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve order details.
    PUT: Update order.
    DELETE: Delete order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

@staff_member_required
def admin_order_detail(request, order_id):
    """Ադմինիստրատորի պատվերի մանրամասների դիտում"""
    order = get_object_or_404(Order, id=order_id)
    return render(
        request, 'admin/orders/order/detail.html', {'order': order}
    )


@staff_member_required
def admin_order_pdf(request, order_id):
    """Պատվերի PDF գեներացիա Ադմինիստրատորի համար"""
    order = get_object_or_404(Order, id=order_id)

    # HTML փոփք էջի ստեղծում
    html = render_to_string('orders/order/pdf.html', {'order': order})

    # PDF պատասխան պատրաստում
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=order_{order.id}.pdf'

    # PDF գեներացման համար WeasyPrint օգտագործում
    try:
        weasyprint.HTML(string=html).write_pdf(
            response,
            stylesheets=[weasyprint.CSS(finders.find('css/pdf.css'))],
        )
    except Exception as e:
        # Սխալի մշակումը PDF գեներացիայում
        messages.error(request, f'Պատվերի PDF ստեղծելու ժամանակ տեղի ունեցավ սխալ: {e}')
        return redirect('admin:orders_order_changelist')

    return response
