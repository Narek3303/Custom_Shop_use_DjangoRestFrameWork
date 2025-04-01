# gdpr/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import GDPRConsent, DataSubjectRequest, DataInventory

@admin.register(GDPRConsent)
class GDPRConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted', 'version', 'timestamp')
    list_filter = ('consent_type', 'granted')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('timestamp', 'ip_address', 'user_agent')

@admin.register(DataSubjectRequest)
class DataSubjectRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'request_type', 'status', 'created_at', 'updated_at')
    list_filter = ('request_type', 'status')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    actions = ['mark_as_completed', 'mark_as_rejected']

    def mark_as_completed(self, request, queryset):
        for dsr in queryset:
            dsr.complete({'action': 'Bulk completion by admin'})
    mark_as_completed.short_description = "Mark selected requests as completed"

    def mark_as_rejected(self, request, queryset):
        for dsr in queryset:
            dsr.reject("Bulk rejection by admin")
    mark_as_rejected.short_description = "Mark selected requests as rejected"

@admin.register(DataInventory)
class DataInventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_category', 'purpose_short', 'retention_period', 'is_sensitive')
    list_filter = ('data_category', 'storage_location', 'is_sensitive')
    search_fields = ('name', 'description', 'purpose')

    def purpose_short(self, obj):
        return obj.purpose[:50] + '...' if len(obj.purpose) > 50 else obj.purpose
    purpose_short.short_description = 'Purpose'