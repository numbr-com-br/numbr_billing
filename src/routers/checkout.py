from flask import Blueprint, request, jsonify
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal

from src.database import Session
from src.dependencies import with_db_session
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


def create_checkout_blueprint():
    bp = Blueprint('checkout', __name__)
    
    @bp.route("/start", methods=["POST"])
    @with_db_session
    def start_checkout(db: Session):
        # Parse request
        data = request.get_json()
        checkout_request = CheckoutRequest.model_validate(data)
        
        # Get plan
        plan = db.get(Plan, checkout_request.plan_id)
        if not plan or not plan.is_active:
            return jsonify({"detail": "Plan not found"}), 404
        
        # Get addons
        addons = []
        if checkout_request.addon_ids:
            result = db.execute(
                select(Addon).where(
                    Addon.id.in_(checkout_request.addon_ids), 
                    Addon.is_active.is_(True)
                )
            )
            addons = result.scalars().all()
        
        # Get plan price based on customer revenue
        plan_price = Decimal("0")
        if checkout_request.customer.annual_revenue is not None:
            # Find the appropriate revenue range for the customer
            query = (
                select(PlanPricing)
                .join(RevenueRange)
                .where(
                    and_(
                        PlanPricing.plan_id == plan.id,
                        RevenueRange.min_revenue <= checkout_request.customer.annual_revenue,
                        (RevenueRange.max_revenue >= checkout_request.customer.annual_revenue)
                        | (RevenueRange.max_revenue.is_(None)),
                    )
                )
            )
            result = db.execute(query)
            plan_pricing = result.scalar_one_or_none()
            
            if not plan_pricing:
                return jsonify({
                    "detail": "No pricing available for the specified revenue range"
                }), 400
            
            plan_price = Decimal(str(plan_pricing.price))
        else:
            return jsonify({
                "detail": "Annual revenue is required for pricing calculation"
            }), 400
        
        # Calculate total price
        total_price = plan_price
        for addon in addons:
            total_price += Decimal(str(addon.price))
        
        # Create or find customer
        result = db.execute(
            select(Customer).where(Customer.email == checkout_request.customer.email)
        )
        customer = result.scalar_one_or_none()
        
        if customer:
            # Update customer info
            customer.name = checkout_request.customer.name
            if checkout_request.customer.cpf_cnpj:
                customer.cpf_cnpj = checkout_request.customer.cpf_cnpj
            if checkout_request.customer.phone:
                customer.phone = checkout_request.customer.phone
            if checkout_request.customer.annual_revenue:
                customer.annual_revenue = checkout_request.customer.annual_revenue
        else:
            # Create new customer
            customer = Customer(
                name=checkout_request.customer.name,
                email=checkout_request.customer.email,
                cpf_cnpj=checkout_request.customer.cpf_cnpj,
                phone=checkout_request.customer.phone,
                annual_revenue=checkout_request.customer.annual_revenue,
            )
            db.add(customer)
        
        db.commit()
        
        # Create customer in Asaas if not exists
        if not customer.asaas_customer_id:
            asaas_customer = asaas_service.create_customer(
                {
                    "name": customer.name,
                    "email": customer.email,
                    "cpfCnpj": customer.cpf_cnpj,
                    "phone": customer.phone,
                }
            )
            customer.asaas_customer_id = asaas_customer["id"]
            db.commit()
        
        # Create subscription
        subscription = Subscription(
            customer_id=customer.id, 
            plan_id=plan.id, 
            status=SubscriptionStatus.PENDING
        )
        db.add(subscription)
        db.commit()
        
        # Add subscription addons
        for addon in addons:
            subscription_addon = SubscriptionAddon(
                subscription_id=subscription.id, 
                addon_id=addon.id, 
                quantity=1
            )
            db.add(subscription_addon)
        
        db.commit()
        
        # Create subscription in Asaas
        next_due_date = datetime.now() + timedelta(days=1)
        asaas_subscription = asaas_service.create_subscription(
            {
                "customer": customer.asaas_customer_id,
                "billingType": checkout_request.billing_type,
                "value": float(total_price),
                "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
                "cycle": plan.cycle.value,
                "description": f"{plan.name} subscription",
            }
        )
        
        # Update subscription with Asaas ID
        subscription.asaas_subscription_id = asaas_subscription["id"]
        subscription.next_due_date = datetime.fromisoformat(asaas_subscription["nextDueDate"])
        db.commit()
        
        # Generate payment link
        payment_link = f"https://www.asaas.com/b/pay/{asaas_subscription['id']}"
        
        response = CheckoutResponse(
            subscription_id=subscription.id, 
            payment_link=payment_link, 
            total_price=total_price
        )
        
        return jsonify(response.model_dump())
    
    @bp.route("/plans", methods=["GET"])
    @with_db_session
    def get_plans(db: Session):
        result = db.execute(
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
        
        return jsonify([pr.model_dump() for pr in plan_responses])
    
    @bp.route("/addons", methods=["GET"])
    @with_db_session
    def get_addons(db: Session):
        result = db.execute(
            select(Addon).where(Addon.is_active.is_(True)).order_by(Addon.price)
        )
        addons = result.scalars().all()
        
        addon_responses = [
            AddonResponse(
                id=addon.id,
                name=addon.name,
                description=addon.description,
                price=addon.price,
                type=addon.type,
            )
            for addon in addons
        ]
        
        return jsonify([ar.model_dump() for ar in addon_responses])
    
    @bp.route("/revenue-ranges", methods=["GET"])
    @with_db_session
    def get_revenue_ranges(db: Session):
        result = db.execute(select(RevenueRange).order_by(RevenueRange.sort_order))
        ranges = result.scalars().all()
        
        range_responses = [
            RevenueRangeResponse(
                id=range.id,
                name=range.name,
                min_revenue=range.min_revenue,
                max_revenue=range.max_revenue,
                sort_order=range.sort_order,
            )
            for range in ranges
        ]
        
        return jsonify([rr.model_dump() for rr in range_responses])
    
    return bp