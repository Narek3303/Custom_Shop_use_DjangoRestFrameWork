from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IPAccessLog, BlockedIP
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=IPAccessLog)
def detect_suspicious_activity(sender, instance, created, **kwargs):
    if not created:
        return

    # Ստուգում ենք վերջին 5 րոպեների մուտքի ձախողումները
    recent_failures = IPAccessLog.objects.filter(
        ip_address=instance.ip_address,
        accessed_at__gte=timezone.now() - timedelta(minutes=5),
        status='blocked'
    ).count()

    if recent_failures > 10:  # 10 ձախողված փորձ 5 րոպեում
        if not BlockedIP.objects.filter(ip_address=instance.ip_address).exists():
            BlockedIP.objects.create(
                ip_address=instance.ip_address,
                reason='Ավտոմատ արգելափակում կասկածելի ակտիվության պատճառով'
            )
