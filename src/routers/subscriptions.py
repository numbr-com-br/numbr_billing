from flask import Blueprint, request, jsonify

from src.database import Session
from src.dependencies import with_db_session
from src.services import SubscriptionService
from src.utils import build_subscription_response, build_subscription_responses


def create_subscriptions_blueprint():
    bp = Blueprint("subscriptions", __name__)

    @bp.route("/<subscription_id>", methods=["GET"])
    @with_db_session
    def get_subscription(db: Session, subscription_id: str):
        service = SubscriptionService(db)
        subscription = service.get_subscription_with_details(subscription_id)
        
        if not subscription:
            return jsonify({"detail": "Subscription not found"}), 404
        
        response = build_subscription_response(subscription, db)
        
        # Add customer info and recent payments for detailed view
        response_dict = response.model_dump()
        response_dict["customer_name"] = subscription.customer.name
        response_dict["customer_email"] = subscription.customer.email
        
        # Get recent payments
        recent_payments = service.get_recent_payments(subscription_id, limit=5)
        response_dict["recent_payments"] = [
            {
                "id": p.id,
                "amount": str(p.amount),
                "status": p.status.value,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "created_at": p.created_at.isoformat()
            }
            for p in recent_payments
        ]
        
        return jsonify(response_dict)

    @bp.route("/<subscription_id>/status", methods=["GET"])
    @with_db_session
    def get_subscription_status(db: Session, subscription_id: str):
        service = SubscriptionService(db)
        subscription = service.get_subscription_with_details(subscription_id)
        
        if not subscription:
            return jsonify({"detail": "Subscription not found"}), 404
        
        return jsonify({
            "subscription_id": subscription_id,
            "status": subscription.status.value,
            "next_due_date": subscription.next_due_date.isoformat() if subscription.next_due_date else None,
            "is_active": subscription.status.value == "ACTIVE"
        })

    @bp.route("/<subscription_id>/cancel", methods=["POST"])
    @with_db_session
    def cancel_subscription(db: Session, subscription_id: str):
        service = SubscriptionService(db)
        
        try:
            subscription = service.cancel_subscription(subscription_id)
            if not subscription:
                return jsonify({"detail": "Subscription not found"}), 404
                
            return jsonify({
                "message": "Subscription canceled successfully",
                "subscription_id": subscription_id,
                "status": subscription.status.value,
                "canceled_at": subscription.canceled_at.isoformat()
            })
        except ValueError as e:
            return jsonify({"detail": str(e)}), 400
        except Exception as e:
            return jsonify({"detail": str(e)}), 500

    @bp.route("/active", methods=["GET"])
    @with_db_session
    def get_active_subscriptions(db: Session):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        service = SubscriptionService(db)
        offset = (page - 1) * per_page
        
        subscriptions, total = service.get_active_subscriptions(offset, per_page)
        
        subscription_responses = build_subscription_responses(subscriptions, db)
        
        return jsonify({
            "subscriptions": [sr.model_dump() for sr in subscription_responses],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        })

    return bp