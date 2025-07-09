from flask import Blueprint, request, jsonify
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.database import Session
from src.dependencies import with_db_session
from src.models import Customer, Subscription, SubscriptionAddon
from src.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerWithSubscriptions,
)
from src.services.asaas import asaas_service
from src.enums import SubscriptionStatus


def create_customers_blueprint():
    bp = Blueprint("customers", __name__)

    @bp.route("", methods=["POST"])
    @with_db_session
    def create_customer(db: Session):
        data = request.get_json()
        customer_data = CustomerCreate.model_validate(data)
        
        result = db.execute(
            select(Customer).where(Customer.email == customer_data.email)
        )
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            for field, value in customer_data.model_dump(exclude_unset=True).items():
                setattr(existing_customer, field, value)
            customer = existing_customer
        else:
            customer = Customer(**customer_data.model_dump())
            db.add(customer)
        
        db.commit()
        
        if not customer.asaas_customer_id:
            try:
                asaas_customer = asaas_service.create_customer({
                    "name": customer.name,
                    "email": customer.email,
                    "cpfCnpj": customer.cpf_cnpj,
                    "phone": customer.phone,
                })
                customer.asaas_customer_id = asaas_customer["id"]
                db.commit()
            except Exception as e:
                print(f"Failed to create Asaas customer: {e}")
        
        response = CustomerResponse.model_validate(customer)
        return jsonify(response.model_dump()), 201 if not existing_customer else 200

    @bp.route("/<customer_id>", methods=["GET"])
    @with_db_session
    def get_customer(db: Session, customer_id: str):
        customer = db.get(Customer, customer_id)
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        active_count = db.execute(
            select(func.count(Subscription.id))
            .where(
                Subscription.customer_id == customer_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).scalar()
        
        total_count = db.execute(
            select(func.count(Subscription.id))
            .where(Subscription.customer_id == customer_id)
        ).scalar()
        
        response = CustomerWithSubscriptions(
            **CustomerResponse.model_validate(customer).model_dump(),
            active_subscriptions_count=active_count,
            total_subscriptions_count=total_count
        )
        
        return jsonify(response.model_dump())

    @bp.route("/email/<email>", methods=["GET"])
    @with_db_session
    def get_customer_by_email(db: Session, email: str):
        result = db.execute(
            select(Customer).where(Customer.email == email)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        active_count = db.execute(
            select(func.count(Subscription.id))
            .where(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).scalar()
        
        total_count = db.execute(
            select(func.count(Subscription.id))
            .where(Subscription.customer_id == customer.id)
        ).scalar()
        
        response = CustomerWithSubscriptions(
            **CustomerResponse.model_validate(customer).model_dump(),
            active_subscriptions_count=active_count,
            total_subscriptions_count=total_count
        )
        
        return jsonify(response.model_dump())

    @bp.route("/<customer_id>", methods=["PUT"])
    @with_db_session
    def update_customer(db: Session, customer_id: str):
        customer = db.get(Customer, customer_id)
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        data = request.get_json()
        update_data = CustomerUpdate.model_validate(data)
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        
        db.commit()
        
        response = CustomerResponse.model_validate(customer)
        return jsonify(response.model_dump())

    @bp.route("/<customer_id>/subscriptions", methods=["GET"])
    @with_db_session
    def get_customer_subscriptions(db: Session, customer_id: str):
        customer = db.get(Customer, customer_id)
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        result = db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon)
            )
            .where(Subscription.customer_id == customer_id)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.scalars().all()
        
        from src.schemas.subscription import SubscriptionResponse, AddonDetail
        from decimal import Decimal
        
        subscription_responses = []
        for sub in subscriptions:
            addon_details = []
            total_addon_price = Decimal("0")
            
            for sa in sub.addons:
                addon_detail = AddonDetail(
                    id=sa.addon.id,
                    name=sa.addon.name,
                    price=sa.addon.price,
                    quantity=sa.quantity,
                    type=sa.addon.type
                )
                addon_details.append(addon_detail)
                total_addon_price += sa.addon.price * sa.quantity
            
            from src.models import PlanPricing
            plan_price_result = db.execute(
                select(PlanPricing.price)
                .where(PlanPricing.plan_id == sub.plan_id)
                .limit(1)
            )
            plan_price = plan_price_result.scalar() or Decimal("0")
            
            total_price = plan_price + total_addon_price
            
            sub_response = SubscriptionResponse(
                id=sub.id,
                customer_id=sub.customer_id,
                plan=sub.plan,
                status=sub.status,
                start_date=sub.start_date,
                next_due_date=sub.next_due_date,
                canceled_at=sub.canceled_at,
                asaas_subscription_id=sub.asaas_subscription_id,
                addons=addon_details,
                total_price=total_price
            )
            subscription_responses.append(sub_response)
        
        return jsonify({
            "subscriptions": [sr.model_dump() for sr in subscription_responses],
            "total": len(subscription_responses)
        })

    @bp.route("/email/<email>/subscriptions", methods=["GET"])
    @with_db_session
    def get_customer_subscriptions_by_email(db: Session, email: str):
        result = db.execute(
            select(Customer).where(Customer.email == email)
        )
        customer = result.scalar_one_or_none()
        
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        result = db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon)
            )
            .where(Subscription.customer_id == customer.id)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.scalars().all()
        
        from src.schemas.subscription import SubscriptionResponse, AddonDetail
        from decimal import Decimal
        
        subscription_responses = []
        for sub in subscriptions:
            addon_details = []
            total_addon_price = Decimal("0")
            
            for sa in sub.addons:
                addon_detail = AddonDetail(
                    id=sa.addon.id,
                    name=sa.addon.name,
                    price=sa.addon.price,
                    quantity=sa.quantity,
                    type=sa.addon.type
                )
                addon_details.append(addon_detail)
                total_addon_price += sa.addon.price * sa.quantity
            
            from src.models import PlanPricing
            plan_price_result = db.execute(
                select(PlanPricing.price)
                .where(PlanPricing.plan_id == sub.plan_id)
                .limit(1)
            )
            plan_price = plan_price_result.scalar() or Decimal("0")
            
            total_price = plan_price + total_addon_price
            
            sub_response = SubscriptionResponse(
                id=sub.id,
                customer_id=sub.customer_id,
                plan=sub.plan,
                status=sub.status,
                start_date=sub.start_date,
                next_due_date=sub.next_due_date,
                canceled_at=sub.canceled_at,
                asaas_subscription_id=sub.asaas_subscription_id,
                addons=addon_details,
                total_price=total_price
            )
            subscription_responses.append(sub_response)
        
        return jsonify({
            "subscriptions": [sr.model_dump() for sr in subscription_responses],
            "total": len(subscription_responses)
        })

    return bp