from flask import Blueprint, request, jsonify

from src.database import Session
from src.dependencies import with_db_session
from src.models import Customer
from src.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerWithSubscriptions,
)
from src.services import CustomerService, SubscriptionService
from src.utils import build_subscription_responses


def create_customers_blueprint():
    bp = Blueprint("customers", __name__)

    @bp.route("", methods=["POST"])
    @with_db_session
    def create_customer(db: Session):
        data = request.get_json()
        customer_data = CustomerCreate.model_validate(data)
        
        service = CustomerService(db)
        customer, is_new = service.create_or_update_customer(customer_data)
        
        response = CustomerResponse.model_validate(customer)
        return jsonify(response.model_dump()), 201 if is_new else 200

    @bp.route("/<customer_id>", methods=["GET"])
    @with_db_session
    def get_customer(db: Session, customer_id: str):
        customer = db.get(Customer, customer_id)
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        service = CustomerService(db)
        active_count, total_count = service.get_customer_subscription_counts(customer_id)
        
        response = CustomerWithSubscriptions(
            **CustomerResponse.model_validate(customer).model_dump(),
            active_subscriptions_count=active_count,
            total_subscriptions_count=total_count
        )
        
        return jsonify(response.model_dump())

    @bp.route("/email/<email>", methods=["GET"])
    @with_db_session
    def get_customer_by_email(db: Session, email: str):
        service = CustomerService(db)
        customer = service.get_customer_by_email(email)
        
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        active_count, total_count = service.get_customer_subscription_counts(customer.id)
        
        response = CustomerWithSubscriptions(
            **CustomerResponse.model_validate(customer).model_dump(),
            active_subscriptions_count=active_count,
            total_subscriptions_count=total_count
        )
        
        return jsonify(response.model_dump())

    @bp.route("/<customer_id>", methods=["PUT"])
    @with_db_session
    def update_customer(db: Session, customer_id: str):
        data = request.get_json()
        update_data = CustomerUpdate.model_validate(data)
        
        service = CustomerService(db)
        customer = service.update_customer(customer_id, update_data)
        
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        response = CustomerResponse.model_validate(customer)
        return jsonify(response.model_dump())

    @bp.route("/<customer_id>/subscriptions", methods=["GET"])
    @with_db_session
    def get_customer_subscriptions(db: Session, customer_id: str):
        customer = db.get(Customer, customer_id)
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        sub_service = SubscriptionService(db)
        subscriptions = sub_service.get_customer_subscriptions(customer_id)
        
        subscription_responses = build_subscription_responses(subscriptions, db)
        
        return jsonify({
            "subscriptions": [sr.model_dump() for sr in subscription_responses],
            "total": len(subscription_responses)
        })

    @bp.route("/email/<email>/subscriptions", methods=["GET"])
    @with_db_session
    def get_customer_subscriptions_by_email(db: Session, email: str):
        service = CustomerService(db)
        customer = service.get_customer_by_email(email)
        
        if not customer:
            return jsonify({"detail": "Customer not found"}), 404
        
        sub_service = SubscriptionService(db)
        subscriptions = sub_service.get_customer_subscriptions(customer.id)
        
        subscription_responses = build_subscription_responses(subscriptions, db)
        
        return jsonify({
            "subscriptions": [sr.model_dump() for sr in subscription_responses],
            "total": len(subscription_responses)
        })

    return bp