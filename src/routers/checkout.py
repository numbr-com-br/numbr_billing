from flask import Blueprint, request, jsonify

from src.database import Session
from src.dependencies import with_db_session
from src.schemas.checkout import CheckoutRequest
from src.services import CheckoutService, CatalogService


def create_checkout_blueprint():
    bp = Blueprint("checkout", __name__)

    @bp.route("/start", methods=["POST"])
    @with_db_session
    def start_checkout(db: Session):
        data = request.get_json()
        checkout_request = CheckoutRequest.model_validate(data)
        
        service = CheckoutService(db)
        
        try:
            response = service.process_checkout(checkout_request)
            return jsonify(response.model_dump())
        except ValueError as e:
            return jsonify({"detail": str(e)}), 400

    @bp.route("/plans", methods=["GET"])
    @with_db_session
    def get_plans(db: Session):
        service = CatalogService(db)
        plan_responses = service.get_active_plans()
        return jsonify([pr.model_dump() for pr in plan_responses])

    @bp.route("/addons", methods=["GET"])
    @with_db_session
    def get_addons(db: Session):
        service = CatalogService(db)
        addon_responses = service.get_active_addons()
        return jsonify([ar.model_dump() for ar in addon_responses])

    @bp.route("/revenue-ranges", methods=["GET"])
    @with_db_session
    def get_revenue_ranges(db: Session):
        service = CatalogService(db)
        range_responses = service.get_revenue_ranges()
        return jsonify([rr.model_dump() for rr in range_responses])

    return bp
