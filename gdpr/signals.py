# gdpr/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import DataSubjectRequest

User = get_user_model()


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """
    Լոգավորում է նոր օգտատերերի ստեղծումը
    """
    if created:
        from .models import DataInventory
        DataInventory.objects.create(
            name="User Registration Data",
            description="Data collected during user registration",
            data_category="personal",
            purpose="User authentication and service provision",
            retention_period="Until account deletion",
            storage_location="db",
            is_sensitive=True,
            collected_from="User registration form",
            model_name="auth.User",
        )


@receiver(pre_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    Մշակում է օգտատերերի ջնջումը GDPR համապատասխան
    """
    from .utils import GDPRUtils
    from .models import DataSubjectRequest

    # Ստեղծում ենք հարցումի գրանցում
    DataSubjectRequest.objects.create(
        user=instance,
        request_type='erasure',
        status='completed',
        request_data={'reason': 'Account deletion'},
        response_data={'action': 'User data anonymized'}
    )

    # Անանունացնում ենք տվյալները
    GDPRUtils.anonymize_user(instance)
