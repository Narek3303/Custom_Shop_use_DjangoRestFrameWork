# erp/services.py
from django.apps import apps
from erp.models import ERPSyncLog
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class ERPSyncService:
    def __init__(self, integration):
        self.integration = integration
        self.adapter = self._get_adapter()

    def _get_adapter(self):
        if self.integration.erp_type == 'odoo':
            from erp.adapters.odoo import OdooAdapter
            return OdooAdapter(self.integration)
        elif self.integration.erp_type == 'sap':
            from erp.adapters.sap import SAPAdapter
            return SAPAdapter(self.integration)
        # Ավելացրեք այլ adapter-ներ ըստ անհրաժեշտության
        raise ValueError(f"Unsupported ERP type: {self.integration.erp_type}")

    def sync_model(self, model_mapping):
        log = ERPSyncLog.objects.create(
            integration=self.integration,
            model_name=model_mapping.django_model,
            status='pending'
        )

        try:
            # 1. Ստանալ տվյալներ ERP-ից
            erp_data = self.adapter.fetch_data(model_mapping.erp_model)

            # 2. Ստանալ Django մոդելի class-ը
            model = apps.get_model(model_mapping.django_model)

            # 3. Synchronize տվյալները
            created = updated = 0
            for item in erp_data:
                django_data = self._map_fields(item, model_mapping.field_mappings)
                obj, created_flag = model.objects.update_or_create(
                    erp_id=item['id'],
                    defaults=django_data
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

            # 4. Update sync log
            log.status = 'success'
            log.record_count = len(erp_data)
            log.details = {
                'created': created,
                'updated': updated
            }

        except Exception as e:
            logger.error(f"ERP sync failed: {str(e)}")
            log.status = 'failed'
            log.error_message = str(e)
        finally:
            log.end_time = timezone.now()
            log.save()
            self.integration.last_sync = timezone.now()
            self.integration.save()

        return log

    def _map_fields(self, erp_data, field_mappings):
        """Map ERP fields to Django model fields"""
        result = {}
        for django_field, erp_field in field_mappings.items():
            if erp_field in erp_data:
                result[django_field] = erp_data[erp_field]
        return result