import logging
from .models import IPAccessLog

logger = logging.getLogger(__name__)

class IPAccessLogger:
    @staticmethod
    def log_access(request, granted):
        client_ip = IPAccessLogger.get_client_ip(request)
        path = request.path
        method = request.method

        IPAccessLog.objects.create(
            ip_address=client_ip,
            path=path,
            method=method,
            status='allowed' if granted else 'blocked',  # Ստատուսի ճիշտ պահպանում
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        if not granted:
            logger.warning(f"❌ Չթույլատրված մուտք: {client_ip} դեպի {path}")

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
