# erp/adapters/base.py
from abc import ABC, abstractmethod
import requests
from django.conf import settings

class ERPAdapter(ABC):
    def __init__(self, integration):
        self.integration = integration
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {integration.api_key}'
        })

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def fetch_data(self, model_name, filters=None):
        pass

    @abstractmethod
    def push_data(self, model_name, data):
        pass

    def make_request(self, method, endpoint, data=None):
        url = f"{self.integration.base_url}/{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ERPSyncError(f"ERP request failed: {str(e)}")

class ERPSyncError(Exception):
    pass
