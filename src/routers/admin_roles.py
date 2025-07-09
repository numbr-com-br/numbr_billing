from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import select

from src.database import Session
from src.dependencies import with_db_session
from src.models.admin_user import AdminRole


def create_admin_roles_blueprint():
    bp = Blueprint("admin_roles", __name__)

    @bp.route("/", methods=["GET"])
    @jwt_required()
    @with_db_session
    def list_roles(db: Session):
        result = db.execute(select(AdminRole).order_by(AdminRole.name))
        roles = result.scalars().all()

        roles_response = []
        for role in roles:
            roles_response.append(
                {
                    "id": role.id,
                    "name": role.name,
                    "permissions": role.permissions,
                    "is_system": role.is_system,
                    "created_at": role.created_at.isoformat() if role.created_at else None,
                    "updated_at": role.updated_at.isoformat() if role.updated_at else None,
                }
            )

        return jsonify(roles_response)

    @bp.route("/<role_id>", methods=["GET"])
    @jwt_required()
    @with_db_session
    def get_role(role_id: str, db: Session):
        role = db.get(AdminRole, role_id)
        if not role:
            return jsonify({"detail": "Role not found"}), 404

        return jsonify(
            {
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions,
                "is_system": role.is_system,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None,
            }
        )

    return bp
