# erp/admin.py
from django.contrib import admin
from .models import ERPIntegration, ERPObjectMapping, ERPSyncLog


@admin.register(ERPIntegration)
class ERPIntegrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'erp_type', 'is_active', 'last_sync')
    list_filter = ('erp_type', 'is_active')
    actions = ['sync_integration']

    def sync_integration(self, request, queryset):
        from erp.services import ERPSyncService
        for integration in queryset:
            ERPSyncService(integration).sync_all()

    sync_integration.short_description = "Sync selected integrations"


@admin.register(ERPObjectMapping)
class ERPObjectMappingAdmin(admin.ModelAdmin):
    list_display = ('integration', 'django_model', 'erp_model')
    list_filter = ('integration',)


@admin.register(ERPSyncLog)
class ERPSyncLogAdmin(admin.ModelAdmin):
    list_display = ('integration', 'model_name', 'status', 'start_time', 'duration')
    list_filter = ('status', 'integration')
    readonly_fields = ('start_time', 'end_time', 'duration')

    def duration(self, obj):
        return obj.duration()

    duration.short_description = 'Duration (seconds)'

