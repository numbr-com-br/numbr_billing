from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

from src.database import get_db
from src.models import (
    Customer,
    Plan,
    Addon,
    Subscription,
    SubscriptionAddon,
    PlanPricing,
    RevenueRange,
)
from src.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
    PlanResponse,
    AddonResponse,
    PlanPricingResponse,
    RevenueRangeResponse,
)
from src.services.asaas import asaas_service
from src.enums import SubscriptionStatus

router = APIRouter(prefix="/api/checkout", tags=["checkout"])


@router.post("/start", response_model=CheckoutResponse)
async def start_checkout(request: CheckoutRequest, db: AsyncSession = Depends(get_db)):
    # Get plan
    plan = await db.get(Plan, request.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get addons
    addons = []
    if request.addon_ids:
        result = await db.execute(
            select(Addon).where(Addon.id.in_(request.addon_ids), Addon.is_active.is_(True))
        )
        addons = result.scalars().all()

    # Get plan price based on customer revenue
    plan_price = Decimal("0")
    if request.customer.annual_revenue is not None:
        # Find the appropriate revenue range for the customer
        query = (
            select(PlanPricing)
            .join(RevenueRange)
            .where(
                and_(
                    PlanPricing.plan_id == plan.id,
                    RevenueRange.min_revenue <= request.customer.annual_revenue,
                    (RevenueRange.max_revenue >= request.customer.annual_revenue)
                    | (RevenueRange.max_revenue.is_(None)),
                )
            )
        )
        result = await db.execute(query)
        plan_pricing = result.scalar_one_or_none()

        if not plan_pricing:
            raise HTTPException(
                status_code=400, detail="No pricing available for the specified revenue range"
            )

        plan_price = Decimal(str(plan_pricing.price))
    else:
        raise HTTPException(
            status_code=400, detail="Annual revenue is required for pricing calculation"
        )

    # Calculate total price
    total_price = plan_price
    for addon in addons:
        total_price += Decimal(str(addon.price))

    # Create or find customer
    result = await db.execute(select(Customer).where(Customer.email == request.customer.email))
    customer = result.scalar_one_or_none()

    if customer:
        # Update customer info
        customer.name = request.customer.name
        if request.customer.cpf_cnpj:
            customer.cpf_cnpj = request.customer.cpf_cnpj
        if request.customer.phone:
            customer.phone = request.customer.phone
        if request.customer.annual_revenue:
            customer.annual_revenue = request.customer.annual_revenue
    else:
        # Create new customer
        customer = Customer(
            name=request.customer.name,
            email=request.customer.email,
            cpf_cnpj=request.customer.cpf_cnpj,
            phone=request.customer.phone,
            annual_revenue=request.customer.annual_revenue,
        )
        db.add(customer)

    await db.commit()

    # Create customer in Asaas if not exists
    if not customer.asaas_customer_id:
        asaas_customer = await asaas_service.create_customer(
            {
                "name": customer.name,
                "email": customer.email,
                "cpfCnpj": customer.cpf_cnpj,
                "phone": customer.phone,
            }
        )
        customer.asaas_customer_id = asaas_customer["id"]
        await db.commit()

    # Create subscription
    subscription = Subscription(
        customer_id=customer.id, plan_id=plan.id, status=SubscriptionStatus.PENDING
    )
    db.add(subscription)
    await db.commit()

    # Add subscription addons
    for addon in addons:
        subscription_addon = SubscriptionAddon(
            subscription_id=subscription.id, addon_id=addon.id, quantity=1
        )
        db.add(subscription_addon)

    await db.commit()

    # Create subscription in Asaas
    next_due_date = datetime.now() + timedelta(days=1)
    asaas_subscription = await asaas_service.create_subscription(
        {
            "customer": customer.asaas_customer_id,
            "billingType": request.billing_type,
            "value": float(total_price),
            "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
            "cycle": plan.cycle.value,
            "description": f"{plan.name} subscription",
        }
    )

    # Update subscription with Asaas ID
    subscription.asaas_subscription_id = asaas_subscription["id"]
    subscription.next_due_date = datetime.fromisoformat(asaas_subscription["nextDueDate"])
    await db.commit()

    # Generate payment link
    payment_link = f"https://www.asaas.com/b/pay/{asaas_subscription['id']}"

    return CheckoutResponse(
        subscription_id=subscription.id, payment_link=payment_link, total_price=total_price
    )


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
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


@router.get("/addons", response_model=List[AddonResponse])
async def get_addons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Addon).where(Addon.is_active.is_(True)).order_by(Addon.price))
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


@router.get("/revenue-ranges", response_model=List[RevenueRangeResponse])
async def get_revenue_ranges(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RevenueRange).order_by(RevenueRange.sort_order))
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
