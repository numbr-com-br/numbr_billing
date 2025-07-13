from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models import Plan, Addon, PlanPricing, RevenueRange


class PricingService:
    """Service layer for pricing calculations and revenue range logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_checkout_price(
        self,
        plan: Plan,
        addons: List[Addon],
        annual_revenue: Optional[Decimal]
    ) -> Decimal:
        """
        Calculate total checkout price based on plan, addons, and revenue.
        """
        if annual_revenue is None:
            raise ValueError("Annual revenue is required for pricing calculation")
        
        # Get plan price based on revenue range
        plan_price = self.get_plan_price_for_revenue(plan.id, annual_revenue)
        
        # Calculate addon prices
        addon_price = sum(Decimal(str(addon.price)) for addon in addons)
        
        return plan_price + addon_price
    
    def get_plan_price_for_revenue(
        self,
        plan_id: str,
        annual_revenue: Decimal
    ) -> Decimal:
        """
        Get plan price based on customer's annual revenue.
        """
        query = (
            select(PlanPricing)
            .join(RevenueRange)
            .where(
                and_(
                    PlanPricing.plan_id == plan_id,
                    RevenueRange.min_revenue <= annual_revenue,
                    (RevenueRange.max_revenue >= annual_revenue) | 
                    (RevenueRange.max_revenue.is_(None))
                )
            )
        )
        result = self.db.execute(query)
        plan_pricing = result.scalar_one_or_none()
        
        if not plan_pricing:
            raise ValueError(
                f"No pricing found for plan {plan_id} "
                f"with revenue {annual_revenue}"
            )
        
        return Decimal(str(plan_pricing.price))
    
    def get_plan_price_by_id(
        self,
        plan_id: str,
        fallback: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Get the first available price for a plan.
        Used when revenue range is not specified.
        """
        result = self.db.execute(
            select(PlanPricing.price)
            .where(PlanPricing.plan_id == plan_id)
            .limit(1)
        )
        price = result.scalar()
        
        return Decimal(str(price)) if price else fallback
    
    def get_revenue_range_for_amount(
        self,
        annual_revenue: Decimal
    ) -> Optional[RevenueRange]:
        """
        Get the revenue range that contains the given annual revenue.
        """
        result = self.db.execute(
            select(RevenueRange)
            .where(
                and_(
                    RevenueRange.min_revenue <= annual_revenue,
                    (RevenueRange.max_revenue >= annual_revenue) | 
                    (RevenueRange.max_revenue.is_(None))
                )
            )
        )
        return result.scalar_one_or_none()
    
    def calculate_subscription_total(
        self,
        plan_id: str,
        addon_quantities: List[tuple[Addon, int]],
        revenue_range_id: Optional[str] = None
    ) -> Decimal:
        """
        Calculate total subscription price with addons and quantities.
        """
        # Get plan base price
        if revenue_range_id:
            result = self.db.execute(
                select(PlanPricing.price)
                .where(
                    and_(
                        PlanPricing.plan_id == plan_id,
                        PlanPricing.revenue_range_id == revenue_range_id
                    )
                )
            )
            plan_price = result.scalar()
            if not plan_price:
                raise ValueError("No pricing found for plan and revenue range")
            plan_price = Decimal(str(plan_price))
        else:
            plan_price = self.get_plan_price_by_id(plan_id)
        
        # Calculate addon prices with quantities
        addon_total = sum(
            Decimal(str(addon.price)) * quantity 
            for addon, quantity in addon_quantities
        )
        
        return plan_price + addon_total