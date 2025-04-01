# erp/adapters/odoo.py
from .base import ERPAdapter, ERPSyncError
import xmlrpc.client

class OdooAdapter(ERPAdapter):
    def authenticate(self):
        try:
            common = xmlrpc.client.ServerProxy(f'{self.integration.base_url}/xmlrpc/2/common')
            self.uid = common.authenticate(
                self.integration.erp_db,  # պետք է ավելացնեք դաշտը ERPIntegration մոդելում
                self.integration.username,
                self.integration.password,
                {}
            )
            self.models = xmlrpc.client.ServerProxy(f'{self.integration.base_url}/xmlrpc/2/object')
            return True
        except Exception as e:
            raise ERPSyncError(f"Odoo authentication failed: {str(e)}")

    def fetch_data(self, model_name, filters=None):
        try:
            return self.models.execute_kw(
                self.integration.erp_db,
                self.uid,
                self.integration.password,
                model_name,
                'search_read',
                [filters or []],
                {'limit': 1000}
            )
        except Exception as e:
            raise ERPSyncError(f"Odoo fetch failed: {str(e)}")

    def push_data(self, model_name, data):
        try:
            if 'id' in data:
                # Update existing record
                return self.models.execute_kw(
                    self.integration.erp_db,
                    self.uid,
                    self.integration.password,
                    model_name,
                    'write',
                    [[data['id']], data]
                )
            else:
                # Create new record
                return self.models.execute_kw(
                    self.integration.erp_db,
                    self.uid,
                    self.integration.password,
                    model_name,
                    'create',
                    [data]
                )
        except Exception as e:
            raise ERPSyncError(f"Odoo push failed: {str(e)}")
