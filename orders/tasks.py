from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import Order

@shared_task
def send_order_status_email(order_id):
    """
    Celery task to send email notification about the order status update.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f"Order #{order.order_id} status updated"
        message = f"Your order status has been updated to {order.status}."
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email],
        )
    except Order.DoesNotExist:
        pass


@shared_task
def send_sms(order_id):
    """
    Celery task to send SMS notification about the order status update.
    """
    try:
        order = Order.objects.get(id=order_id)
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Order #{order.order_id} status updated to {order.status}.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=order.customer.phone_number,
        )
    except Order.DoesNotExist:
        pass