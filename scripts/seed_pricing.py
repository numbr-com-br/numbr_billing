#!/usr/bin/env python3
"""
Seed script to populate revenue ranges and plan pricing
"""
import os
import sys
import asyncio
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import AsyncSessionLocal
from src.models import Plan, RevenueRange, PlanPricing
from sqlalchemy import select, delete


async def main():
    async with AsyncSessionLocal() as db:
        # Clear existing data
        await db.execute(delete(PlanPricing))
        await db.execute(delete(RevenueRange))
        await db.commit()
        
        # Create revenue ranges
        revenue_ranges = [
            {
                "name": "Microempresa",
                "min_revenue": Decimal("0"),
                "max_revenue": Decimal("360000"),  # Até R$ 360.000/ano
                "sort_order": 1
            },
            {
                "name": "Pequena Empresa",
                "min_revenue": Decimal("360000.01"),
                "max_revenue": Decimal("4800000"),  # Até R$ 4.8 milhões/ano
                "sort_order": 2
            },
            {
                "name": "Média Empresa",
                "min_revenue": Decimal("4800000.01"),
                "max_revenue": Decimal("50000000"),  # Até R$ 50 milhões/ano
                "sort_order": 3
            },
            {
                "name": "Grande Empresa",
                "min_revenue": Decimal("50000000.01"),
                "max_revenue": None,  # Acima de R$ 50 milhões/ano
                "sort_order": 4
            }
        ]
        
        created_ranges = []
        for range_data in revenue_ranges:
            revenue_range = RevenueRange(**range_data)
            db.add(revenue_range)
            created_ranges.append(revenue_range)
        
        await db.commit()
        
        # Get all active plans
        result = await db.execute(select(Plan).where(Plan.is_active == True))
        plans = result.scalars().all()
        
        if not plans:
            print("No active plans found. Please seed plans first.")
            return
        
        # Define pricing multipliers for each revenue range
        pricing_multipliers = {
            "Microempresa": Decimal("1.0"),
            "Pequena Empresa": Decimal("1.5"),
            "Média Empresa": Decimal("2.0"),
            "Grande Empresa": Decimal("3.0")
        }
        
        # Base prices for plans (used as reference)
        base_prices = {
            "Starter": Decimal("49.90"),
            "Professional": Decimal("99.90"),
            "Enterprise": Decimal("299.90")
        }
        
        # Create plan pricing for each combination
        for plan in plans:
            base_price = base_prices.get(plan.name, Decimal("99.90"))
            
            for revenue_range in created_ranges:
                multiplier = pricing_multipliers[revenue_range.name]
                price = base_price * multiplier
                
                plan_pricing = PlanPricing(
                    plan_id=plan.id,
                    revenue_range_id=revenue_range.id,
                    price=price
                )
                db.add(plan_pricing)
        
        await db.commit()
        
        print("✅ Revenue ranges and plan pricing seeded successfully!")
        
        # Display created data
        print("\n📊 Revenue Ranges:")
        for rr in created_ranges:
            max_str = f"R$ {rr.max_revenue:,.2f}" if rr.max_revenue else "Unlimited"
            print(f"  - {rr.name}: R$ {rr.min_revenue:,.2f} - {max_str}")
        
        print("\n💰 Plan Pricing:")
        for plan in plans:
            print(f"\n  {plan.name}:")
            result = await db.execute(
                select(PlanPricing)
                .join(RevenueRange)
                .where(PlanPricing.plan_id == plan.id)
                .order_by(RevenueRange.sort_order)
            )
            pricings = result.scalars().all()
            
            for pp in pricings:
                await db.refresh(pp, ["revenue_range"])
                print(f"    - {pp.revenue_range.name}: R$ {pp.price:,.2f}/month")


if __name__ == "__main__":
    asyncio.run(main())