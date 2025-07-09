from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from src.enums import SubscriptionStatus, BillingCycle, PaymentStatus, AddonType


class PaymentSummary(BaseModel):
    id: str
    amount: Decimal
    status: PaymentStatus
    due_date: datetime
    paid_at: Optional[datetime]
    billing_type: str

    class Config:
        from_attributes = True


class AddonDetail(BaseModel):
    id: str
    name: str
    price: Decimal
    quantity: int
    type: AddonType


class PlanDetail(BaseModel):
    id: str
    name: str
    description: Optional[str]
    cycle: BillingCycle

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    plan: PlanDetail
    status: SubscriptionStatus
    start_date: datetime
    next_due_date: Optional[datetime]
    canceled_at: Optional[datetime]
    asaas_subscription_id: Optional[str]
    addons: List[AddonDetail] = []
    total_price: Decimal
    
    class Config:
        from_attributes = True


class SubscriptionDetailResponse(SubscriptionResponse):
    customer_name: str
    customer_email: str
    recent_payments: List[PaymentSummary] = []
    

class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionResponse]
    total: int