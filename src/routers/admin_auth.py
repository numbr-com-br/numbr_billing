from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    unset_jwt_cookies,
)
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import Optional

from src.database import Session
from src.dependencies import with_db_session
from src.models.admin_user import AdminUser, AdminSession
from src.schemas.admin_auth import (
    LoginRequest,
    AdminUserResponse,
    ChangePasswordRequest,
    SessionResponse,
)
from src.admin.auth import (
    authenticate_user,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


def create_session_record_with_info(
    db: Session,
    user: AdminUser,
    token_jti: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AdminSession:
    """Create a session record with explicit IP and user agent info"""
    session = AdminSession(
        user_id=user.id,
        token_jti=token_jti,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    db.add(session)
    db.commit()
    return session


def create_admin_auth_blueprint():
    bp = Blueprint("admin_auth", __name__)

    @bp.route("/login", methods=["GET", "POST"])
    @with_db_session
    def login(db: Session):
        if request.method == "GET":
            next_url = request.args.get("next")
            return render_template("admin/login.html", next=next_url)

        is_json_request = request.is_json

        if is_json_request:
            data = request.get_json()
            login_request = LoginRequest.model_validate(data)
            email = login_request.email
            password = login_request.password
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        user = authenticate_user(db, email, password)
        if not user:
            if is_json_request:
                return jsonify({"detail": "Invalid email or password"}), 401
            else:
                flash("Invalid email or password", "error")
                return redirect(url_for("admin_auth.login"))

        x_forwarded_for = request.headers.get("X-Forwarded-For")
        ip_address = (
            x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.remote_addr
        )
        user_agent = request.headers.get("User-Agent", "Unknown")

        additional_claims = {
            "email": user.email,
            "is_superuser": user.is_superuser,
            "roles": [role.name for role in user.roles],
        }

        access_token = create_access_token(
            identity=str(user.id), additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=str(user.id), additional_claims=additional_claims
        )

        from flask_jwt_extended import decode_token

        decoded = decode_token(access_token)
        token_jti = decoded.get("jti")

        create_session_record_with_info(db, user, token_jti, ip_address, user_agent)

        if is_json_request:
            response = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": AdminUserResponse.model_validate(user).model_dump(),
            }
            return jsonify(response)
        else:
            response = redirect(request.form.get("next") or url_for("admin.index"))
            set_access_cookies(response, access_token)
            flash(f"Welcome back, {user.full_name or user.email}!", "success")
            return response

    @bp.route("/logout", methods=["GET", "POST"])
    @jwt_required(optional=True)
    @with_db_session
    def logout(db: Session):
        identity = get_jwt_identity()
        if identity:
            jti = get_jwt().get("jti")
            if jti:
                stmt = (
                    update(AdminSession)
                    .where(AdminSession.token_jti == jti)
                    .values(revoked_at=datetime.utcnow())
                )
                db.execute(stmt)
                db.commit()

        is_json_request = (
            request.is_json
            or request.method == "POST"
            and request.headers.get("Content-Type") == "application/json"
        )

        if is_json_request:
            return jsonify({"message": "Successfully logged out"})
        else:
            response = redirect(url_for("admin_auth.login"))
            unset_jwt_cookies(response)
            flash("You have been logged out successfully.", "info")
            return response

    @bp.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    @with_db_session
    def refresh(db: Session):
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        additional_claims = {
            "email": claims.get("email"),
            "is_superuser": claims.get("is_superuser"),
            "role_id": claims.get("role_id"),
        }

        new_access_token = create_access_token(
            identity=current_user_id, additional_claims=additional_claims
        )

        user = db.get(AdminUser, current_user_id)
        if user:
            from flask_jwt_extended import decode_token

            decoded = decode_token(new_access_token)
            token_jti = decoded.get("jti")

            ip_address = request.remote_addr
            user_agent = request.headers.get("User-Agent", "Unknown")

            create_session_record_with_info(db, user, token_jti, ip_address, user_agent)

        return jsonify({"access_token": new_access_token})

    @bp.route("/me", methods=["GET"])
    @jwt_required()
    @with_db_session
    def get_current_user_info(db: Session):
        current_user_id = get_jwt_identity()

        user = db.get(AdminUser, current_user_id)
        if not user:
            return jsonify({"detail": "User not found"}), 404

        return jsonify(AdminUserResponse.model_validate(user).model_dump())

    @bp.route("/change-password", methods=["POST"])
    @jwt_required()
    @with_db_session
    def change_password(db: Session):
        current_user_id = get_jwt_identity()
        data = request.get_json()
        password_request = ChangePasswordRequest.model_validate(data)

        user = db.get(AdminUser, current_user_id)
        if not user:
            return jsonify({"detail": "User not found"}), 404

        if not verify_password(password_request.current_password, user.password_hash):
            return jsonify({"detail": "Current password is incorrect"}), 400

        user.password_hash = get_password_hash(password_request.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        stmt = (
            update(AdminSession)
            .where(AdminSession.user_id == user.id)
            .where(AdminSession.revoked_at.is_(None))
            .values(revoked_at=datetime.utcnow())
        )
        db.execute(stmt)
        db.commit()

        return jsonify({"message": "Password changed successfully"})

    @bp.route("/sessions", methods=["GET"])
    @jwt_required()
    @with_db_session
    def get_active_sessions(db: Session):
        current_user_id = get_jwt_identity()

        result = db.execute(
            select(AdminSession)
            .where(AdminSession.user_id == current_user_id)
            .where(AdminSession.revoked_at.is_(None))
            .where(AdminSession.expires_at > datetime.utcnow())
            .order_by(AdminSession.created_at.desc())
        )
        sessions = result.scalars().all()

        session_responses = [
            SessionResponse.model_validate(session).model_dump() for session in sessions
        ]

        return jsonify(session_responses)

    return bp
