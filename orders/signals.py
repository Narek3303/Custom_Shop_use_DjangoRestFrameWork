from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Order

@receiver(post_save, sender=Order)
def send_order_confirmation_email(sender, instance, created, **kwargs):
    if created:
        subject = f'Order Confirmation #{instance.id}'
        message = f'Hello {instance.first_name},\n\nYour order #{instance.id} has been placed successfully.'
        send_mail(subject, message, 'admin@myshop.com', [instance.email])