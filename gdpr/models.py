# gdpr/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()

class GDPRConsent(models.Model):
    """
    Համաձայնության կառավարման մոդել
    """
    CONSENT_TYPES = (
        ('privacy_policy', 'Privacy Policy'),
        ('terms_of_service', 'Terms of Service'),
        ('marketing', 'Marketing Communications'),
        ('cookies', 'Cookie Consent'),
        ('analytics', 'Analytics Tracking'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gdpr_consents'
    )
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    granted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'consent_type')
        verbose_name = 'GDPR Consent'
        verbose_name_plural = 'GDPR Consents'

    def __str__(self):
        return f"{self.user} - {self.get_consent_type_display()} ({'Granted' if self.granted else 'Denied'})"


class DataSubjectRequest(models.Model):
    """
    Տվյալների սուբյեկտի հարցումների մոդել
    """
    REQUEST_TYPES = (
        ('access', 'Data Access Request'),
        ('rectification', 'Data Rectification'),
        ('erasure', 'Right to be Forgotten'),
        ('restriction', 'Restriction of Processing'),
        ('portability', 'Data Portability'),
        ('object', 'Right to Object'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gdpr_requests'
    )
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Data Subject Request'
        verbose_name_plural = 'Data Subject Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.get_request_type_display()} ({self.get_status_display()})"

    def complete(self, response_data=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if response_data:
            self.response_data = response_data
        self.save()

    def reject(self, reason):
        self.status = 'rejected'
        self.response_data = {'reason': reason}
        self.save()


class DataInventory(models.Model):
    """
    Տվյալների գույքագրում - ինչ տվյալներ ենք հավաքում և որտեղ են պահվում
    """
    DATA_CATEGORIES = (
        ('personal', 'Personal Data'),
        ('contact', 'Contact Information'),
        ('financial', 'Financial Data'),
        ('behavioral', 'Behavioral Data'),
        ('technical', 'Technical Data'),
    )

    STORAGE_LOCATIONS = (
        ('db', 'Primary Database'),
        ('backup', 'Backup Storage'),
        ('analytics', 'Analytics Service'),
        ('crm', 'CRM System'),
        ('marketing', 'Marketing Platform'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    data_category = models.CharField(max_length=50, choices=DATA_CATEGORIES)
    purpose = models.TextField()
    retention_period = models.CharField(max_length=100)
    storage_location = models.CharField(max_length=50, choices=STORAGE_LOCATIONS)
    is_sensitive = models.BooleanField(default=False)
    collected_from = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100, blank=True)
    field_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Data Inventory'
        verbose_name_plural = 'Data Inventory'
        ordering = ['data_category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_data_category_display()})"


