from flask import Blueprint, request, jsonify
from sqlalchemy import select
from datetime import datetime
import hashlib
import hmac

from src.database import Session
from src.dependencies import with_db_session
from src.models import Payment, Subscription, WebhookLog
from src.config import settings
from src.enums import PaymentStatus, SubscriptionStatus


def verify_webhook_signature(payload: str, signature: str) -> bool:
    expected_signature = hmac.new(
        settings.asaas_webhook_token.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def map_asaas_payment_status(asaas_status: str) -> PaymentStatus:
    status_map = {
        "PENDING": PaymentStatus.PENDING,
        "CONFIRMED": PaymentStatus.CONFIRMED,
        "RECEIVED": PaymentStatus.RECEIVED,
        "OVERDUE": PaymentStatus.OVERDUE,
        "REFUNDED": PaymentStatus.REFUNDED,
        "RECEIVED_IN_CASH": PaymentStatus.RECEIVED,
        "REFUND_REQUESTED": PaymentStatus.REFUNDED,
        "CHARGEBACK_REQUESTED": PaymentStatus.FAILED,
        "CHARGEBACK_DISPUTE": PaymentStatus.FAILED,
        "AWAITING_CHARGEBACK_REVERSAL": PaymentStatus.FAILED,
        "DUNNING_REQUESTED": PaymentStatus.FAILED,
        "DUNNING_RECEIVED": PaymentStatus.RECEIVED,
        "AWAITING_RISK_ANALYSIS": PaymentStatus.PENDING,
    }
    return status_map.get(asaas_status, PaymentStatus.FAILED)


def create_webhook_blueprint():
    bp = Blueprint('webhooks', __name__)
    
    @bp.route("/asaas", methods=["POST"])
    @with_db_session
    def handle_asaas_webhook(db: Session):
        payload = request.get_data(as_text=True)
        
        signature = request.headers.get("asaas-signature", "")
        if not verify_webhook_signature(payload, signature):
            return jsonify({"detail": "Invalid webhook signature"}), 401
        
        data = request.get_json()
        event = data.get("event")
        payment_data = data.get("payment", {})
        
        webhook_log = WebhookLog(event=event, payload=data, success=True)
        
        try:
            if event in ["PAYMENT_CREATED", "PAYMENT_UPDATED", "PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"]:
                asaas_payment_id = payment_data.get("id")
                subscription_id = payment_data.get("subscription")
                
                if asaas_payment_id and subscription_id:
                    result = db.execute(
                        select(Subscription).where(
                            Subscription.asaas_subscription_id == subscription_id
                        )
                    )
                    subscription = result.scalar_one_or_none()
                    
                    if subscription:
                        result = db.execute(
                            select(Payment).where(Payment.asaas_payment_id == asaas_payment_id)
                        )
                        payment = result.scalar_one_or_none()
                        
                        if not payment:
                            payment = Payment(
                                subscription_id=subscription.id,
                                asaas_payment_id=asaas_payment_id,
                                amount=payment_data.get("value", 0),
                                due_date=datetime.fromisoformat(payment_data.get("dueDate")),
                                status=map_asaas_payment_status(payment_data.get("status")),
                                billing_type=payment_data.get("billingType"),
                                description=payment_data.get("description"),
                                external_reference=payment_data.get("externalReference"),
                            )
                            db.add(payment)
                        else:
                            payment.status = map_asaas_payment_status(payment_data.get("status"))
                            if payment_data.get("confirmedDate"):
                                payment.paid_at = datetime.fromisoformat(
                                    payment_data.get("confirmedDate")
                                )
                            payment.invoice_number = payment_data.get("invoiceNumber")
                            payment.transaction_receipt = payment_data.get("transactionReceiptUrl")
                        
                        if payment.status == PaymentStatus.RECEIVED:
                            subscription.status = SubscriptionStatus.ACTIVE
                        elif payment.status == PaymentStatus.OVERDUE:
                            subscription.status = SubscriptionStatus.INACTIVE
            
            db.add(webhook_log)
            db.commit()
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            webhook_log.success = False
            webhook_log.error = str(e)
            db.add(webhook_log)
            db.commit()
            return jsonify({"detail": "Failed to process webhook"}), 500
    
    return bp