from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.database import Session
from src.models.admin_user import AdminUser, AdminSession
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

JWT_SECRET_KEY = settings.jwt_secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[AdminUser]:
    """Authenticate user with email and password"""
    result = db.execute(
        select(AdminUser).where(AdminUser.email == email).options(selectinload(AdminUser.roles))
    )
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None

    return user


def get_user_by_id(db: Session, user_id: str) -> Optional[AdminUser]:
    """Get user by ID"""
    result = db.execute(
        select(AdminUser).where(AdminUser.id == user_id).options(selectinload(AdminUser.roles))
    )
    return result.scalar_one_or_none()


def verify_token_session(db: Session, jti: str) -> bool:
    """Verify that token session is valid and not logged out"""
    session_result = db.execute(
        select(AdminSession).where(
            and_(
                AdminSession.token_jti == jti,
                AdminSession.revoked_at.is_(None),
                AdminSession.expires_at > datetime.utcnow(),
            )
        )
    )
    return session_result.scalar_one_or_none() is not None


def create_session_record(
    db: Session,
    user: AdminUser,
    token_jti: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AdminSession:
    """Create a session record for tracking"""
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


def logout_session(db: Session, jti: str) -> None:
    """Mark session as logged out"""
    result = db.execute(select(AdminSession).where(AdminSession.token_jti == jti))
    session = result.scalar_one_or_none()

    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()


def cleanup_expired_sessions(db: Session) -> int:
    """Clean up expired sessions - should be run periodically"""
    from sqlalchemy import delete

    result = db.execute(delete(AdminSession).where(AdminSession.expires_at < datetime.utcnow()))
    db.commit()
    return result.rowcount
