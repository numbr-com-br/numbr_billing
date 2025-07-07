import httpx
from typing import Dict, Any, List
from src.config import settings


class AsaasService:
    def __init__(self):
        self.base_url = settings.asaas_api_url
        self.api_key = settings.asaas_api_key
        self.headers = {"access_token": self.api_key, "Content-Type": "application/json"}

    def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/customers", json=data, headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/customers/{customer_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def create_subscription(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/subscriptions", json=data, headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/subscriptions/{subscription_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def cancel_subscription(self, subscription_id: str) -> None:
        with httpx.Client() as client:
            response = client.delete(
                f"{self.base_url}/subscriptions/{subscription_id}", headers=self.headers
            )
            response.raise_for_status()

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/payments/{payment_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    def get_subscription_payments(self, subscription_id: str) -> List[Dict[str, Any]]:
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/subscriptions/{subscription_id}/payments", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

    def create_payment_link(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/paymentLinks", json=data, headers=self.headers
            )
            response.raise_for_status()
            return response.json()


asaas_service = AsaasService()