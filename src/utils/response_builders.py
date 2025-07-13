from typing import List
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Subscription, PlanPricing
from src.schemas.subscription import SubscriptionResponse, AddonDetail


def build_subscription_response(
    subscription: Subscription,
    db: Session
) -> SubscriptionResponse:
    """
    Build a SubscriptionResponse with addon details and total price calculation.
    This eliminates duplicated code across multiple routers.
    """
    addon_details = []
    total_addon_price = Decimal("0")
    
    for sub_addon in subscription.addons:
        addon_detail = AddonDetail(
            id=sub_addon.addon.id,
            name=sub_addon.addon.name,
            price=sub_addon.addon.price,
            quantity=sub_addon.quantity,
            type=sub_addon.addon.type
        )
        addon_details.append(addon_detail)
        total_addon_price += sub_addon.addon.price * sub_addon.quantity
    
    # Get plan base price
    plan_price_result = db.execute(
        select(PlanPricing.price)
        .where(PlanPricing.plan_id == subscription.plan_id)
        .limit(1)
    )
    plan_price = plan_price_result.scalar() or Decimal("0")
    
    total_price = plan_price + total_addon_price
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan=subscription.plan,
        status=subscription.status,
        start_date=subscription.start_date,
        next_due_date=subscription.next_due_date,
        canceled_at=subscription.canceled_at,
        asaas_subscription_id=subscription.asaas_subscription_id,
        addons=addon_details,
        total_price=total_price
    )


def build_subscription_responses(
    subscriptions: List[Subscription],
    db: Session
) -> List[SubscriptionResponse]:
    """Build a list of subscription responses."""
    return [
        build_subscription_response(sub, db) 
        for sub in subscriptions
    ]