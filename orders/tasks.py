from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

from .models import Order
from django.template.loader import render_to_string


@shared_task
def send_order_confirmation_email(order_id):
    """
    Celery task to send order confirmation email.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Order Confirmation: {order.id}'
        context = {
            'order': order,
            'total_price': order.get_total_cost(),
            'order_items': order.items.all(),
        }
        message = render_to_string('order/email/order_confirmation.html', context)

        mail_sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=False,
        )

        if mail_sent:
            return f"Order {order.id} confirmation email sent successfully."
        else:
            return f"Failed to send confirmation email for order {order.id}."
    except Order.DoesNotExist:
        return f"Order with ID {order_id} not found."
    except Exception as e:
        return f"An error occurred while sending email: {str(e)}"


@shared_task
def mark_order_as_paid(order_id):
    """
    Celery task to mark order as paid.
    """
    try:
        order = Order.objects.get(id=order_id)
        order.paid = True
        order.save()
        return f"Order {order.id} marked as paid successfully."
    except Order.DoesNotExist:
        return f"Order with ID {order_id} not found."
    except Exception as e:
        return f"An error occurred while updating order status: {str(e)}"