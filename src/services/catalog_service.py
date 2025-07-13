from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models import Plan, Addon, PlanPricing, RevenueRange
from src.schemas.checkout import (
    PlanResponse,
    AddonResponse,
    PlanPricingResponse,
    RevenueRangeResponse,
)


class CatalogService:
    """Service layer for catalog operations (plans, addons, revenue ranges)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_plans(self) -> List[PlanResponse]:
        """Get all active plans with their pricing information."""
        result = self.db.execute(
            select(Plan)
            .options(selectinload(Plan.plan_pricings).selectinload(PlanPricing.revenue_range))
            .where(Plan.is_active.is_(True))
            .order_by(Plan.name)
        )
        plans = result.scalars().all()
        
        plan_responses = []
        for plan in plans:
            pricing_list = []
            for pp in sorted(plan.plan_pricings, key=lambda x: x.revenue_range.sort_order):
                pricing_list.append(
                    PlanPricingResponse(
                        revenue_range_id=pp.revenue_range_id,
                        revenue_range_name=pp.revenue_range.name,
                        min_revenue=pp.revenue_range.min_revenue,
                        max_revenue=pp.revenue_range.max_revenue,
                        price=pp.price,
                    )
                )
            
            plan_responses.append(
                PlanResponse(
                    id=plan.id,
                    name=plan.name,
                    description=plan.description,
                    cycle=plan.cycle,
                    features=plan.features or [],
                    pricing=pricing_list,
                )
            )
        
        return plan_responses
    
    def get_active_addons(self) -> List[AddonResponse]:
        """Get all active addons."""
        result = self.db.execute(
            select(Addon)
            .where(Addon.is_active.is_(True))
            .order_by(Addon.price)
        )
        addons = result.scalars().all()
        
        return [
            AddonResponse(
                id=addon.id,
                name=addon.name,
                description=addon.description,
                price=addon.price,
                type=addon.type,
            )
            for addon in addons
        ]
    
    def get_revenue_ranges(self) -> List[RevenueRangeResponse]:
        """Get all revenue ranges."""
        result = self.db.execute(
            select(RevenueRange)
            .order_by(RevenueRange.sort_order)
        )
        ranges = result.scalars().all()
        
        return [
            RevenueRangeResponse(
                id=range.id,
                name=range.name,
                min_revenue=range.min_revenue,
                max_revenue=range.max_revenue,
                sort_order=range.sort_order,
            )
            for range in ranges
        ]