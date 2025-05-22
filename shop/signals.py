from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Product


@receiver(m2m_changed, sender=Product.related_products.through)
def sync_related_products(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in ("post_add", "post_remove"):
        for related_id in pk_set:
            try:
                related_product = Product.objects.get(id=related_id)
            except Product.DoesNotExist:
                # During loaddata, related product may not be created yet.
                continue

            if action == "post_add":
                for p in instance.related_products.all():
                    if p.id != related_product.id:
                        related_product.related_products.add(p)
                        p.related_products.add(related_product)

                related_product.related_products.add(instance)

            elif action == "post_remove":
                for p in instance.related_products.all():
                    if p.id != related_product.id:
                        related_product.related_products.remove(p)
                        p.related_products.remove(related_product)

                related_product.related_products.remove(instance)
