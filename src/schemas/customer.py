from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class CustomerBase(BaseModel):
    name: str
    email: str
    cpf_cnpj: Optional[str] = None
    phone: Optional[str] = None
    annual_revenue: Optional[Decimal] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    phone: Optional[str] = None
    annual_revenue: Optional[Decimal] = None


class CustomerResponse(CustomerBase):
    id: str
    asaas_customer_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerWithSubscriptions(CustomerResponse):
    active_subscriptions_count: int
    total_subscriptions_count: int