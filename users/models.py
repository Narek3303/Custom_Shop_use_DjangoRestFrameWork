from authemail.models import EmailUserManager, EmailAbstractUser
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _



class CustomUser(EmailAbstractUser):
        # Custom fields
        date_of_birth = models.DateField('Date of birth', null=True, blank=True)

        # Required
        objects = EmailUserManager()


User = settings.AUTH_USER_MODEL




class UserProfileManager(models.Manager):
        """Custom Manager for UserProfile"""


        def with_phone(self):
                return self.exclude(phone_number__isnull=True).exclude(phone_number="")


class UserProfile(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
        phone_number = models.CharField(
                max_length=20,
                blank=True,
                null=True,
                validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$", message=_("Invalid phone number"))],
        )
        address = models.TextField(blank=True, null=True)
        city = models.CharField(max_length=100, blank=True, null=True)
        country = models.CharField(max_length=100, blank=True, null=True)
        postal_code = models.CharField(max_length=20, blank=True, null=True)
        birth_date = models.DateField(blank=True, null=True)
        avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
        email_verified = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        objects = UserProfileManager()  # Custom Manager

        class Meta:
                verbose_name = "User Profile"
                verbose_name_plural = "User Profiles"

        def __str__(self):
                return f"{self.user} - Profile"

        def get_full_address(self):
                """Returns formatted full address"""
                return f"{self.address}, {self.city}, {self.country}, {self.postal_code}" if self.address else "No address provided"


        def is_complete_profile(self):
                """Checks if profile has all essential details"""
                required_fields = [self.phone_number, self.address, self.city, self.country, self.birth_date]
                return all(required_fields)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when new user is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
