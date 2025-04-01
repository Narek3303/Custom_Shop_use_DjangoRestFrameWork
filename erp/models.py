# erp/models.py
from django.db import models
from django.utils import timezone

class ERPIntegration(models.Model):
    ERP_CHOICES = [
        ('odoo', 'Odoo'),
        ('sap', 'SAP'),
        ('dynamics', 'Microsoft Dynamics'),
        ('netsuite', 'NetSuite'),
    ]

    name = models.CharField(max_length=50)
    erp_type = models.CharField(max_length=20, choices=ERP_CHOICES)
    base_url = models.URLField()
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_interval = models.PositiveIntegerField(default=60)  # րոպեներով

    def __str__(self):
        return f"{self.get_erp_type_display()} - {self.name}"

class ERPObjectMapping(models.Model):
    integration = models.ForeignKey(ERPIntegration, on_delete=models.CASCADE)
    django_model = models.CharField(max_length=100)
    erp_model = models.CharField(max_length=100)
    field_mappings = models.JSONField()  # {'django_field': 'erp_field'}

    class Meta:
        unique_together = ('integration', 'django_model')

class ERPSyncLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]

    integration = models.ForeignKey(ERPIntegration, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    model_name = models.CharField(max_length=100)
    record_count = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict)

    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


