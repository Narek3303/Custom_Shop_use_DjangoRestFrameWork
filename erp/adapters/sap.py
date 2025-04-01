# erp/adapters/sap.py
from .base import ERPAdapter, ERPSyncError

class SAPAdapter(ERPAdapter):
    def authenticate(self):
        # SAP-ը սովորաբար օգտագործում է Basic Auth կամ OAuth
        self.session.auth = (self.integration.username, self.integration.password)
        try:
            response = self.session.get(f"{self.integration.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            raise ERPSyncError(f"SAP authentication failed: {str(e)}")

    def fetch_data(self, model_name, filters=None):
        endpoint = f"{model_name}?$format=json"
        if filters:
            endpoint += f"&$filter={filters}"
        try:
            response = self.make_request('GET', endpoint)
            return response.get('d', {}).get('results', [])
        except Exception as e:
            raise ERPSyncError(f"SAP fetch failed: {str(e)}")

    def push_data(self, model_name, data):
        try:
            response = self.make_request('POST', model_name, data)
            return response.get('d', {})
        except Exception as e:
            raise ERPSyncError(f"SAP push failed: {str(e)}")

