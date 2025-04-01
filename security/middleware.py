from django.http import HttpResponseForbidden
from django.conf import settings
from ipaddress import ip_network, ip_address
from django.utils import timezone
from django.db.models import Q
from .models import AllowedIP, BlockedIP, IPAccessLog
import logging

logger = logging.getLogger(__name__)


class IPWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip = self.get_client_ip(request)

        # Log the access attempt
        self.log_access(request, client_ip)

        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempt: {client_ip}")
            return HttpResponseForbidden("Your IP address has been blocked")

        # Check if IP is allowed
        if not self.is_ip_allowed(client_ip):
            logger.warning(f"Unauthorized IP attempt: {client_ip}")
            return HttpResponseForbidden("Your IP address is not authorized")

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_ip_allowed(self, ip):
        # Check settings.ALLOWED_IPS first
        for allowed in getattr(settings, "ALLOWED_IPS", []):
            try:
                if ip_address(ip) in ip_network(allowed):
                    return True
            except ValueError:
                continue

        # Check database records
        now = timezone.now()
        allowed_ips = AllowedIP.objects.filter(
            Q(ip_address=ip) | Q(ip_network__isnull=False),
            is_active=True,
            expires_at__gte=now
        )

        for allowed_ip in allowed_ips:
            if allowed_ip.ip_network:
                try:
                    if ip_address(ip) in ip_network(allowed_ip.ip_network):
                        return True
                except ValueError:
                    continue

        return False

    def is_ip_blocked(self, ip):
        return BlockedIP.objects.filter(ip_address=ip).exists()  # Removed `is_active=True`

    def log_access(self, request, ip):
        IPAccessLog.objects.create(
            ip_address=ip,
            path=request.path,
            method=request.method,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            accessed_at=timezone.now()
        )
