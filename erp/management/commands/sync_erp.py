# erp/management/commands/sync_erp.py
from django.core.management.base import BaseCommand
from erp.models import ERPIntegration, ERPObjectMapping
from erp.services import ERPSyncService


class Command(BaseCommand):
    help = 'Synchronize data with ERP systems'

    def handle(self, *args, **options):
        integrations = ERPIntegration.objects.filter(is_active=True)

        for integration in integrations:
            self.stdout.write(f"Syncing with {integration.name} ({integration.get_erp_type_display()})")

            service = ERPSyncService(integration)
            mappings = ERPObjectMapping.objects.filter(integration=integration)

            for mapping in mappings:
                self.stdout.write(f"  Syncing model: {mapping.django_model} -> {mapping.erp_model}")
                log = service.sync_model(mapping)

                if log.status == 'success':
                    self.stdout.write(self.style.SUCCESS(
                        f"    Success: {log.record_count} records processed"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"    Failed: {log.error_message}"
                    ))
