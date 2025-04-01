from functools import wraps
from django.http import HttpResponseForbidden
from django.conf import settings
from ipaddress import ip_address, ip_network

def get_client_ip(request):
    """ Ստանում է հաճախորդի իրական IP հասցեն, հաշվի առնելով reverse proxy-ները """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def ip_whitelist_required(view_func):
    """ Դեկորատոր, որը թույլ է տալիս մուտքը միայն որոշակի IP-ներից """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        client_ip = get_client_ip(request)

        allowed_ips = getattr(settings, "ALLOWED_IPS", [])
        if not isinstance(allowed_ips, (list, set, tuple)):
            allowed_ips = []

        # Ստուգում ենք, արդյոք IP-ն գտնվում է թույլատրվածների ցուցակում
        for allowed in allowed_ips:
            try:
                if ip_address(client_ip) in ip_network(allowed, strict=False):
                    return view_func(request, *args, **kwargs)
            except ValueError:
                continue

        return HttpResponseForbidden("IP not authorized")

    return _wrapped_view
