from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import select

from src.database import Session
from src.dependencies import with_db_session
from src.models.admin_user import AdminUser
from src.schemas.admin_auth import AdminUserResponse


def create_admin_users_blueprint():
    bp = Blueprint("admin_users", __name__)

    @bp.route("/", methods=["GET"])
    @jwt_required()
    @with_db_session
    def list_users(db: Session):
        # Check permissions
        claims = get_jwt()
        if not claims.get("is_superuser"):
            return jsonify({"detail": "Not enough permissions"}), 403

        result = db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
        users = result.scalars().all()

        users_response = [AdminUserResponse.model_validate(user).model_dump() for user in users]

        return jsonify(users_response)

    @bp.route("/<user_id>", methods=["GET"])
    @jwt_required()
    @with_db_session
    def get_user(user_id: str, db: Session):
        # Check permissions
        claims = get_jwt()
        current_user_id = get_jwt_identity()

        # Users can view their own profile, admins can view all
        if user_id != current_user_id and not claims.get("is_superuser"):
            return jsonify({"detail": "Not enough permissions"}), 403

        user = db.get(AdminUser, user_id)
        if not user:
            return jsonify({"detail": "User not found"}), 404

        return jsonify(AdminUserResponse.model_validate(user).model_dump())

    @bp.route("/<user_id>", methods=["DELETE"])
    @jwt_required()
    @with_db_session
    def delete_user(user_id: str, db: Session):
        # Check permissions
        claims = get_jwt()
        if not claims.get("is_superuser"):
            return jsonify({"detail": "Not enough permissions"}), 403

        user = db.get(AdminUser, user_id)
        if not user:
            return jsonify({"detail": "User not found"}), 404

        # Don't allow self-deletion
        current_user_id = get_jwt_identity()
        if user_id == current_user_id:
            return jsonify({"detail": "Cannot delete yourself"}), 400

        db.delete(user)
        db.commit()

        return jsonify({"message": "User deleted successfully"})

    return bp
