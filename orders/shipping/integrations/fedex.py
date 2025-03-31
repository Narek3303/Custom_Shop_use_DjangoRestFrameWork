import requests
import logging
from django.conf import settings
from requests.exceptions import RequestException
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FedExIntegrationError(Exception):
    """Custom exception for FedEx integration errors"""
    pass


class FedExIntegration:
    def __init__(self):
        if not all([
            settings.FEDEX_API_KEY,
            settings.FEDEX_API_SECRET,
            settings.FEDEX_ACCOUNT_NUMBER,
            settings.FEDEX_BASE_URL
        ]):
            raise FedExIntegrationError("FedEx API credentials are not properly configured")

        self.api_key = settings.FEDEX_API_KEY
        self.api_secret = settings.FEDEX_API_SECRET
        self.base_url = settings.FEDEX_BASE_URL
        self.account_number = settings.FEDEX_ACCOUNT_NUMBER
        self.auth_token = None
        self.token_expiry = None

    def _get_auth_token(self):
        """Authenticate with FedEx API and get access token"""
        # Check if we have a valid cached token
        if self.auth_token and self.token_expiry and self.token_expiry > datetime.now():
            return self.auth_token

        auth_url = f"{self.base_url}/oauth/token"

        try:
            response = requests.post(
                auth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            response.raise_for_status()

            auth_data = response.json()
            self.auth_token = auth_data.get('access_token')
            expires_in = auth_data.get('expires_in', 3600)  # Default to 1 hour if not provided
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # Subtract 5 min buffer

            if not self.auth_token:
                raise FedExIntegrationError("Failed to obtain auth token from FedEx")

            return self.auth_token

        except RequestException as e:
            logger.error(f"FedEx authentication failed: {str(e)}")
            raise FedExIntegrationError("FedEx authentication failed") from e

    def get_rates(self, origin, destination, package):
        """
        Get shipping rates from FedEx API

        Args:
            origin: dict with 'postal_code' and 'country_code'
            destination: dict with 'postal_code', 'country_code', and optional 'residential'
            package: dict with 'weight' (kg), 'length', 'width', 'height' (cm)

        Returns:
            dict: Parsed rate response or None if failed
        """
        try:
            token = self._get_auth_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'X-locale': 'en_US'
            }

            payload = self._build_rate_request(origin, destination, package)

            response = requests.post(
                f"{self.base_url}/rate/v1/rates/quotes",
                json=payload,
                headers=headers,
                timeout=10  # 10 second timeout
            )

            response.raise_for_status()
            return self._parse_rate_response(response.json())

        except RequestException as e:
            logger.error(f"FedEx API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in FedEx integration: {str(e)}")
            return None

    def _build_rate_request(self, origin, destination, package):
        """Build the rate request payload"""
        return {
            "accountNumber": {"value": self.account_number},
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "postalCode": origin['postal_code'],
                        "countryCode": origin['country_code']
                    }
                },
                "recipient": {
                    "address": {
                        "postalCode": destination['postal_code'],
                        "countryCode": destination['country_code'],
                        "residential": destination.get('residential', False)
                    }
                },
                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",  # Or "USE_SCHEDULED_PICKUP"
                "rateRequestType": ["LIST", "ACCOUNT"],
                "preferredCurrency": "USD",
                "packageCount": "1",
                "requestedPackageLineItems": [{
                    "groupPackageCount": "1",
                    "weight": {
                        "units": "KG",
                        "value": package['weight']
                    },
                    "dimensions": {
                        "length": package['length'],
                        "width": package['width'],
                        "height": package['height'],
                        "units": "CM"
                    }
                }]
            }
        }

    def _parse_rate_response(self, response):
        """Parse and extract relevant data from FedEx response"""
        if not response or 'output' not in response:
            return None

        output = response['output']
        rates = []

        for rate_reply in output.get('rateReplyDetails', []):
            for detail in rate_reply.get('ratedShipmentDetails', []):
                if 'totalNetCharge' in detail['shipmentRateDetail']:
                    rate = {
                        'service_type': rate_reply.get('serviceType'),
                        'service_name': rate_reply.get('serviceName'),
                        'delivery_date': rate_reply.get('deliveryTimestamp'),
                        'total_charge': detail['shipmentRateDetail']['totalNetCharge']['amount'],
                        'currency': detail['shipmentRateDetail']['totalNetCharge']['currency'],
                        'transit_time': rate_reply.get('transitTime'),
                        'commit_details': rate_reply.get('commit', {})
                    }
                    rates.append(rate)

        return {
            'rates': rates,
            'transaction_id': output.get('transactionId'),
            'customer_transaction_id': output.get('customerTransactionId')
        }

    def create_shipment(self, order, shipping_details):
        """Create a shipment label and tracking"""
        # Implementation for creating actual shipment
        pass

    def track_shipment(self, tracking_number):
        """Track an existing shipment"""
        # Implementation for tracking
        pass