from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    is_used = models.BooleanField(default=False)  # Ավելացնում ենք դաշտը՝ արդյոք կուպոնը օգտագործված է
    is_one_time_use = models.BooleanField(default=True)  # Եթե կուպոնը մեկ անգամ է օգտագործվում
    valid_to = models.DateTimeField()
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage value (0 to 100)',
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Coupon {self.code} ({self.discount}% off)"

    def is_valid(self):
        """
        Checks if the coupon is valid based on its date range and active status.
        """
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"




'''
    {
    "message": "Coupon applied successfully!",
    "coupon_id": 1,
    "discount": 15,
    "valid_from": "2025-03-01T00:00:00Z",
    "valid_to": "2025-05-01T00:00:00Z"
}


{
    "error": "Invalid coupon",
    "details": {
        "code": ["This coupon has expired."]
    }
}
'''