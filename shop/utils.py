from django.core.mail import send_mail
from django.utils.timezone import now
from django.db.models import F
from .models import Product, Wishlist
from celery import shared_task

def send_discount_notifications():
    # Գտնել բոլոր ապրանքները, որոնց զեղչը մեծ է 0-ի
    discounted_products = Product.objects.filter(discount_percentage__gt=0)

    for product in discounted_products:
        # Գտնել բոլոր wishlist-ները, որտեղ այդ ապրանքն է ու դեռ չեն ծանուցվել
        wishlisted_users = Wishlist.objects.filter(product=product, notified=False)

        for wishlist in wishlisted_users:
            user_email = wishlist.user.email
            subject = f"📢 Զեղչ {product.name}-ի վրա!"
            message = f"Բարև {wishlist.user.first_name or wishlist.user.email},\n\n" \
                      f"Ձեր wishlist-ում գտնվող {product.name}-ը այժմ ունի {product.discount_percentage}% զեղչ:\n" \
                      f"Վերջնական գինը՝ {product.get_final_price()} AMD\n" \
                      f"Դիտեք այստեղ՝ {product.get_absolute_url()}\n\n" \
                      f"Շտապեք, քանի դեռ առաջարկը գործում է!"

            send_mail(subject, message, 'noreply@yourshop.com', [user_email])

            # Նշել, որ օգտատերը ծանուցվել է
            wishlist.notified = True
            wishlist.save()



@shared_task
def send_discount_notifications_task():
    send_discount_notifications()