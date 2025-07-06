#!/usr/bin/env python3
"""
Seed script to populate plans
"""
import os
import sys
import asyncio
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import AsyncSessionLocal
from src.models import Plan
from src.enums import BillingCycle
from sqlalchemy import select, delete


async def main():
    async with AsyncSessionLocal() as db:
        # Check if plans already exist
        result = await db.execute(select(Plan))
        existing_plans = result.scalars().all()
        
        if existing_plans:
            print(f"Found {len(existing_plans)} existing plans")
            return
        
        # Create plans
        plans = [
            {
                "name": "Starter",
                "description": "Ideal para pequenos negócios e freelancers",
                "cycle": BillingCycle.MONTHLY,
                "features": [
                    "Até 50 clientes",
                    "Até 100 cobranças/mês",
                    "Notificações por e-mail",
                    "Suporte por e-mail"
                ]
            },
            {
                "name": "Professional",
                "description": "Para empresas em crescimento",
                "cycle": BillingCycle.MONTHLY,
                "features": [
                    "Até 500 clientes",
                    "Até 1000 cobranças/mês",
                    "Notificações por e-mail e SMS",
                    "Relatórios avançados",
                    "API completa",
                    "Suporte prioritário"
                ]
            },
            {
                "name": "Enterprise",
                "description": "Para grandes empresas com necessidades específicas",
                "cycle": BillingCycle.MONTHLY,
                "features": [
                    "Clientes ilimitados",
                    "Cobranças ilimitadas",
                    "Notificações multicanal",
                    "Relatórios personalizados",
                    "API completa com rate limit aumentado",
                    "Gerente de conta dedicado",
                    "SLA garantido",
                    "Customizações"
                ]
            }
        ]
        
        for plan_data in plans:
            plan = Plan(**plan_data)
            db.add(plan)
        
        await db.commit()
        
        print("✅ Plans seeded successfully!")
        
        # Display created plans
        result = await db.execute(select(Plan))
        created_plans = result.scalars().all()
        
        print("\n📋 Created Plans:")
        for plan in created_plans:
            print(f"  - {plan.name}: {plan.description}")
            print(f"    Cycle: {plan.cycle.value}")
            print(f"    Features: {len(plan.features)} included")


if __name__ == "__main__":
    asyncio.run(main())