# gdpr/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import DataInventory


class GDPRDataInventoryMiddleware(MiddlewareMixin):
    """
    Middleware որ լոգավորում է տվյալների հավաքումը
    """

    def process_request(self, request):
        # Ստուգում ենք եթե դա POST հարցում է (տվյալների հավաքում)
        if request.method == 'POST':
            try:
                view_func, _, _ = resolve(request.path)
                view_name = f"{view_func.__module__}.{view_func.__name__}"

                # Ստուգում ենք view-ի անունը որոշելու համար ինչ տեսակի տվյալներ են հավաքվում
                if 'registration' in view_name.lower():
                    self._log_data_collection(request, 'User Registration', 'personal')
                elif 'profile' in view_name.lower():
                    self._log_data_collection(request, 'Profile Update', 'personal')
                # Ավելացրեք լրացուցիչ պայմաններ այստեղ

            except:
                pass

    def _log_data_collection(self, request, source, data_category):
        """
        Լոգավորում է տվյալների հավաքումը DataInventory-ում
        """
        if not request.user.is_authenticated:
            return

        DataInventory.objects.create(
            name=f"Data collection from {source}",
            description=f"Data collected via {request.path}",
            data_category=data_category,
            purpose="User-provided data for service operation",
            retention_period="Until account deletion",
            storage_location="db",
            is_sensitive=True,
            collected_from=request.path,
            model_name="Various",
        )
