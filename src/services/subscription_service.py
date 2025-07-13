from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from src.models import Subscription, SubscriptionAddon, Payment
from src.enums import SubscriptionStatus
from src.services.asaas import asaas_service


class SubscriptionService:
    """Service layer for subscription-related business logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_subscription_with_details(
        self, 
        subscription_id: str
    ) -> Optional[Subscription]:
        """Get subscription with all related data loaded."""
        result = self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.customer),
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon),
                selectinload(Subscription.payments)
            )
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    def get_customer_subscriptions(
        self, 
        customer_id: str
    ) -> List[Subscription]:
        """Get all subscriptions for a customer."""
        result = self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon)
            )
            .where(Subscription.customer_id == customer_id)
            .order_by(Subscription.created_at.desc())
        )
        return result.scalars().all()
    
    def get_active_subscriptions(
        self, 
        offset: int = 0, 
        limit: int = 20
    ) -> tuple[List[Subscription], int]:
        """
        Get paginated active subscriptions.
        Returns tuple of (subscriptions, total_count).
        """
        # Count total
        count_query = select(func.count()).select_from(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .subquery()
        )
        total = self.db.execute(count_query).scalar()
        
        # Get paginated results
        result = self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.customer),
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon)
            )
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .offset(offset)
            .limit(limit)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.scalars().all()
        
        return subscriptions, total
    
    def cancel_subscription(
        self, 
        subscription_id: str
    ) -> Optional[Subscription]:
        """Cancel a subscription."""
        subscription = self.db.get(Subscription, subscription_id)
        
        if not subscription:
            return None
        
        if subscription.status in [
            SubscriptionStatus.CANCELED, 
            SubscriptionStatus.INACTIVE
        ]:
            raise ValueError("Subscription is already canceled or inactive")
        
        # Cancel in Asaas first
        if subscription.asaas_subscription_id:
            try:
                asaas_service.cancel_subscription(subscription.asaas_subscription_id)
            except Exception as e:
                raise Exception(f"Failed to cancel subscription in Asaas: {str(e)}")
        
        # Update local record
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        self.db.commit()
        
        return subscription
    
    def get_recent_payments(
        self, 
        subscription_id: str, 
        limit: int = 5
    ) -> List[Payment]:
        """Get recent payments for a subscription."""
        result = self.db.execute(
            select(Payment)
            .where(Payment.subscription_id == subscription_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    def create_subscription_addons(
        self, 
        subscription_id: str, 
        addon_ids: List[str]
    ) -> None:
        """Create subscription addons."""
        for addon_id in addon_ids:
            subscription_addon = SubscriptionAddon(
                subscription_id=subscription_id,
                addon_id=addon_id,
                quantity=1
            )
            self.db.add(subscription_addon)
        self.db.commit()