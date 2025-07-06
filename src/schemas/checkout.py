from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from src.enums import BillingCycle, AddonType, SubscriptionStatus


class CustomerRequest(BaseModel):
    name: str
    email: str
    cpf_cnpj: Optional[str] = None
    phone: Optional[str] = None
    annual_revenue: Optional[Decimal] = None


class CheckoutRequest(BaseModel):
    plan_id: str
    addon_ids: List[str] = Field(default_factory=list)
    customer: CustomerRequest
    billing_type: str = Field(pattern="^(BOLETO|CREDIT_CARD|PIX)$")


class CheckoutResponse(BaseModel):
    subscription_id: str
    payment_link: str
    total_price: Decimal


class RevenueRangeResponse(BaseModel):
    id: str
    name: str
    min_revenue: Decimal
    max_revenue: Optional[Decimal]
    sort_order: int


class PlanPricingResponse(BaseModel):
    revenue_range_id: str
    revenue_range_name: str
    min_revenue: Decimal
    max_revenue: Optional[Decimal]
    price: Decimal


class PlanResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    cycle: BillingCycle
    features: List[str]
    pricing: List[PlanPricingResponse]


class AddonResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: Decimal
    type: AddonType


class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    next_due_date: Optional[datetime]
    total_price: Decimal
