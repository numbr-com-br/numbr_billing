import httpx
from typing import Dict, Any, List
from src.config import settings


class AsaasService:
    def __init__(self):
        self.base_url = settings.asaas_api_url
        self.api_key = settings.asaas_api_key
        self.headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/customers",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/{customer_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_subscription(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subscriptions",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def cancel_subscription(self, subscription_id: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
            response.raise_for_status()
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_subscription_payments(self, subscription_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subscriptions/{subscription_id}/payments",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
    
    async def create_payment_link(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/paymentLinks",
                json=data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


asaas_service = AsaasService()