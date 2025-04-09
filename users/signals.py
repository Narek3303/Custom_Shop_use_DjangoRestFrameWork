from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth

User = get_user_model()

@receiver(post_save, sender=User)
def verify_social_user(sender, instance, created, **kwargs):
    """
    Եթե user-ը social login-ով է գրանցվել, ապա նրան հաստատված ենք համարում։
    """
    if created:
        # Ստուգում ենք՝ արդյո՞ք user-ը social login-ով է գրանցվել
        if UserSocialAuth.objects.filter(user=instance).exists():
            instance.is_verified = True
            instance.save()
