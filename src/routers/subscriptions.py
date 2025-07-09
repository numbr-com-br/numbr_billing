from flask import Blueprint, request, jsonify
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from decimal import Decimal

from src.database import Session
from src.dependencies import with_db_session
from src.models import Subscription, Payment, PlanPricing, SubscriptionAddon
from src.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionDetailResponse,
    PaymentSummary,
    AddonDetail,
)
from src.enums import SubscriptionStatus


def create_subscriptions_blueprint():
    bp = Blueprint("subscriptions", __name__)

    @bp.route("/<subscription_id>", methods=["GET"])
    @with_db_session
    def get_subscription(db: Session, subscription_id: str):
        result = db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.customer),
                selectinload(Subscription.plan),
                selectinload(Subscription.addons).selectinload(SubscriptionAddon.addon),
                selectinload(Subscription.payments)
            )
            .where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return jsonify({"detail": "Subscription not found"}), 404
        
        addon_details = []
        total_addon_price = Decimal("0")
        
        for sa in subscription.addons:
            addon_detail = AddonDetail(
                id=sa.addon.id,
                name=sa.addon.name,
                price=sa.addon.price,
                quantity=sa.quantity,
                type=sa.addon.type
            )
            addon_details.append(addon_detail)
            total_addon_price += sa.addon.price * sa.quantity
        
        plan_price_result = db.execute(
            select(PlanPricing.price)
            .where(PlanPricing.plan_id == subscription.plan_id)
            .limit(1)
        )
        plan_price = plan_price_result.scalar() or Decimal("0")
        
        total_price = plan_price + total_addon_price
        
        recent_payments = sorted(
            subscription.payments, 
            key=lambda p: p.created_at, 
            reverse=True
        )[:5]
        
        payment_summaries = [
            PaymentSummary.model_validate(payment) 
            for payment in recent_payments
        ]
        
        response = SubscriptionDetailResponse(
            id=subscription.id,
            customer_id=subscription.customer_id,
            customer_name=subscription.customer.name,
            customer_email=subscription.customer.email,
            plan=subscription.plan,
            status=subscription.status,
            start_date=subscription.start_date,
            next_due_date=subscription.next_due_date,
            canceled_at=subscription.canceled_at,
            asaas_subscription_id=subscription.asaas_subscription_id,
            addons=addon_details,
            total_price=total_price,
            recent_payments=payment_summaries
        )
        
        return jsonify(response.model_dump())

    @bp.route("/<subscription_id>/status", methods=["GET"])
    @with_db_session
    def get_subscription_status(db: Session, subscription_id: str):
        result = db.execute(
            select(Subscription.status, Subscription.next_due_date)
            .where(Subscription.id == subscription_id)
        )
        row = result.one_or_none()
        
        if not row:
            return jsonify({"detail": "Subscription not found"}), 404
        
        status, next_due_date = row
        
        return jsonify({
            "subscription_id": subscription_id,
            "status": status.value,
            "next_due_date": next_due_date.isoformat() if next_due_date else None,
            "is_active": status == SubscriptionStatus.ACTIVE
        })

    @bp.route("/<subscription_id>/cancel", methods=["POST"])
    @with_db_session
    def cancel_subscription(db: Session, subscription_id: str):
        subscription = db.get(Subscription, subscription_id)
        
        if not subscription:
            return jsonify({"detail": "Subscription not found"}), 404
        
        if subscription.status in [SubscriptionStatus.CANCELED, SubscriptionStatus.INACTIVE]:
            return jsonify({"detail": "Subscription is already canceled or inactive"}), 400
        
        if subscription.asaas_subscription_id:
            try:
                from src.services.asaas import asaas_service
                asaas_service.cancel_subscription(subscription.asaas_subscription_id)
            except Exception as e:
                return jsonify({"detail": f"Failed to cancel subscription in Asaas: {str(e)}"}), 500
        
        from datetime import datetime
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            "message": "Subscription canceled successfully",
            "subscription_id": subscription_id,
            "status": subscription.status.value,
            "canceled_at": subscription.canceled_at.isoformat()
        })

    @bp.route("/active", methods=["GET"])
    @with_db_session
    def get_active_subscriptions(db: Session):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = select(Subscription).options(
            selectinload(Subscription.customer),
            selectinload(Subscription.plan)
        ).where(Subscription.status == SubscriptionStatus.ACTIVE)
        
        total = db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar()
        
        result = db.execute(
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.scalars().all()
        
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
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        })

    return bp