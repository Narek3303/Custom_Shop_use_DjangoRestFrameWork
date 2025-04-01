# views.py
from .decorators import ip_whitelist_required


@ip_whitelist_required
def sensitive_api_view(request):
    # Ձեր կոդը այստեղ
    return JsonResponse({"status": "success"})