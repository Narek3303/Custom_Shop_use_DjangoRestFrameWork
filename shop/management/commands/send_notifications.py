from django.core.management.base import BaseCommand
from shop.utils import send_discount_notifications

class Command(BaseCommand):
    help = 'Ուղարկում է զեղչված wishlist ապրանքների մասին ծանուցումներ'

    def handle(self, *args, **kwargs):
        send_discount_notifications()
        self.stdout.write(self.style.SUCCESS('✅ Էլփոստի ծանուցումները ուղարկվեցին'))