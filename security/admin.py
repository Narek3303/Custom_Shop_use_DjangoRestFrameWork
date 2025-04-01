from django.contrib import admin
from .models import AllowedIP, BlockedIP, IPAccessLog, SuspiciousIPPattern
from django.utils import timezone


@admin.register(AllowedIP)
class AllowedIPAdmin(admin.ModelAdmin):
    list_display = ('ip_info', 'description', 'is_active', 'expires_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('ip_address', 'ip_network', 'description')
    actions = ['activate_selected', 'deactivate_selected']

    def ip_info(self, obj):
        return obj.ip_address if obj.ip_address else obj.ip_network or "N/A"

    ip_info.short_description = 'IP/Network'

    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)

    activate_selected.short_description = "Activate selected IPs"

    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)

    deactivate_selected.short_description = "Deactivate selected IPs"


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reason', 'blocked_at')
    search_fields = ('ip_address', 'reason')
    actions = ['block_selected', 'unblock_selected']

    def block_selected(self, request, queryset):
        queryset.update(is_active=True)

    block_selected.short_description = "Block selected IPs"

    def unblock_selected(self, request, queryset):
        queryset.update(is_active=False)

    unblock_selected.short_description = "Unblock selected IPs"


@admin.register(IPAccessLog)
class IPAccessLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'path', 'method', 'status', 'accessed_at')
    list_filter = ('status', 'method')
    search_fields = ('ip_address', 'path')
    readonly_fields = ('ip_address', 'path', 'method', 'user_agent', 'accessed_at')
    date_hierarchy = 'accessed_at'


@admin.register(SuspiciousIPPattern)
class SuspiciousIPPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'reason', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('pattern', 'reason')
