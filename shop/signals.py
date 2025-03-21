from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Product


@receiver(m2m_changed, sender=Product.related_products.through)
def sync_related_products(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in ("post_add", "post_remove"):
        for related_id in pk_set:
            related_product = Product.objects.get(id=related_id)

            for p in instance.related_products.all():
                related_product.related_products.add(p)
                p.related_products.add(related_product)


            related_product.related_products.add(instance)

    elif action == "post_remove":
        for related_id in pk_set:
            related_product = Product.objects.get(id=related_id)


            for p in instance.related_products.all():
                related_product.related_products.remove(p)
                p.related_products.remove(related_product)

            related_product.related_products.remove(instance)