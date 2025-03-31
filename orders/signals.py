from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .utils.pdf_generator import generate_invoice_pdf

@receiver(post_save, sender=Order)
def create_invoice_on_order_completion(sender, instance, created, **kwargs):
    if instance.status == 'completed' and not hasattr(instance, 'invoice'):
        generate_invoice_pdf(instance, save_to_file=True)