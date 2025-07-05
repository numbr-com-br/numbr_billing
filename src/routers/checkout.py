from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

from src.database import get_db
from src.models import Customer, Plan, Addon, Subscription, SubscriptionAddon
from src.schemas.checkout import (
    CheckoutRequest, CheckoutResponse, PlanResponse, AddonResponse
)
from src.services.asaas import asaas_service
from src.enums import SubscriptionStatus

router = APIRouter(prefix="/api/checkout", tags=["checkout"])


@router.post("/start", response_model=CheckoutResponse)
async def start_checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    # Get plan
    plan = await db.get(Plan, request.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get addons
    addons = []
    if request.addon_ids:
        result = await db.execute(
            select(Addon).where(
                Addon.id.in_(request.addon_ids),
                Addon.is_active == True
            )
        )
        addons = result.scalars().all()
    
    # Calculate total price
    total_price = Decimal(str(plan.price))
    for addon in addons:
        total_price += Decimal(str(addon.price))
    
    # Create or find customer
    result = await db.execute(
        select(Customer).where(Customer.email == request.customer.email)
    )
    customer = result.scalar_one_or_none()
    
    if customer:
        # Update customer info
        customer.name = request.customer.name
        if request.customer.cpf_cnpj:
            customer.cpf_cnpj = request.customer.cpf_cnpj
        if request.customer.phone:
            customer.phone = request.customer.phone
    else:
        # Create new customer
        customer = Customer(
            name=request.customer.name,
            email=request.customer.email,
            cpf_cnpj=request.customer.cpf_cnpj,
            phone=request.customer.phone
        )
        db.add(customer)
    
    await db.commit()
    
    # Create customer in Asaas if not exists
    if not customer.asaas_customer_id:
        asaas_customer = await asaas_service.create_customer({
            "name": customer.name,
            "email": customer.email,
            "cpfCnpj": customer.cpf_cnpj,
            "phone": customer.phone
        })
        customer.asaas_customer_id = asaas_customer["id"]
        await db.commit()
    
    # Create subscription
    subscription = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status=SubscriptionStatus.PENDING
    )
    db.add(subscription)
    await db.commit()
    
    # Add subscription addons
    for addon in addons:
        subscription_addon = SubscriptionAddon(
            subscription_id=subscription.id,
            addon_id=addon.id,
            quantity=1
        )
        db.add(subscription_addon)
    
    await db.commit()
    
    # Create subscription in Asaas
    next_due_date = datetime.now() + timedelta(days=1)
    asaas_subscription = await asaas_service.create_subscription({
        "customer": customer.asaas_customer_id,
        "billingType": request.billing_type,
        "value": float(total_price),
        "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
        "cycle": plan.cycle.value,
        "description": f"{plan.name} subscription"
    })
    
    # Update subscription with Asaas ID
    subscription.asaas_subscription_id = asaas_subscription["id"]
    subscription.next_due_date = datetime.fromisoformat(asaas_subscription["nextDueDate"])
    await db.commit()
    
    # Generate payment link
    payment_link = f"https://www.asaas.com/b/pay/{asaas_subscription['id']}"
    
    return CheckoutResponse(
        subscription_id=subscription.id,
        payment_link=payment_link,
        total_price=total_price
    )


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.price)
    )
    plans = result.scalars().all()
    
    return [
        PlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            price=plan.price,
            cycle=plan.cycle,
            features=plan.features or []
        )
        for plan in plans
    ]


@router.get("/addons", response_model=List[AddonResponse])
async def get_addons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Addon).where(Addon.is_active == True).order_by(Addon.price)
    )
    addons = result.scalars().all()
    
    return [
        AddonResponse(
            id=addon.id,
            name=addon.name,
            description=addon.description,
            price=addon.price,
            type=addon.type
        )
        for addon in addons
    ]