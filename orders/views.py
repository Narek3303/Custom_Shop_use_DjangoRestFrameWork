from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .tasks import send_order_confirmation_email, mark_order_as_paid


class OrderViewSet(viewsets.ModelViewSet):
    """Order ViewSet to handle CRUD operations."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        """Override to perform create and set additional data."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get items related to a specific order."""
        order = self.get_object()
        items = OrderItem.objects.filter(order=order)
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Mark the order as paid and send a confirmation email."""
        order = self.get_object()
        # Mark the order as paid
        order.paid = True
        order.save()

        # Call the Celery task to send email notification
        send_order_confirmation_email.delay(order.id)

        return Response({'status': 'Order marked as paid, confirmation email sent.'}, status=status.HTTP_200_OK)


class OrderItemViewSet(viewsets.ModelViewSet):
    """OrderItem ViewSet to handle CRUD operations for order items."""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def perform_create(self, serializer):
        """Override to perform create and set additional data."""
        serializer.save()