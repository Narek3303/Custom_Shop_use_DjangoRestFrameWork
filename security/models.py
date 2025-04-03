# models.py
from django.db import models

from django.db import models
from ipaddress import ip_network, ip_address
from django.core.exceptions import ValidationError

class IPNetworkField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 18  # Max length for CIDR notation (e.g., "192.168.1.0/24")
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        try:
            ip_network(value)
        except ValueError:
            raise ValidationError("Invalid CIDR notation for IP network")

class AllowedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True, null=True, blank=True)
    ip_network = IPNetworkField(unique=True, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # New: expiration time

    def clean(self):
        if not self.ip_address and not self.ip_network:
            raise ValidationError("Either IP address or IP network must be specified")
        if self.ip_address and self.ip_network:
            raise ValidationError("Can't specify both IP address and IP network")

    def __str__(self):
        display = self.ip_address if self.ip_address else self.ip_network
        return f"{display} ({'active' if self.is_active else 'inactive'})"

class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


# middleware.py
def is_ip_blocked(self, ip):
    from .models import BlockedIP
    return BlockedIP.objects.filter(ip_address=ip).exists()


# models.py
class IPAccessLog(models.Model):
    ip_address = models.GenericIPAddressField()
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # pending/allowed/blocked

    class Meta:
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['accessed_at']),
        ]
        ordering = ['-accessed_at']


class SuspiciousIPPattern(models.Model):
    pattern = models.CharField(max_length=100)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def match(self, ip):
        # Implement your pattern matching logic
        pass


