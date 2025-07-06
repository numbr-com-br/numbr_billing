from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.database import get_db as get_session
from src.models.admin_user import AdminUser, AdminSession
from src.config import settings
import uuid

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT Configuration
ALGORITHM = "HS256"  # Will be replaced with ES256 in production
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Use JWT secret key from settings
JWT_SECRET_KEY = settings.jwt_secret_key


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())  # JWT ID for blacklisting
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
) -> Optional[AdminUser]:
    """Authenticate user with email and password"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(AdminUser)
        .where(AdminUser.email == email)
        .options(selectinload(AdminUser.roles))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> AdminUser:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        jti: str = payload.get("jti")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Check if token is blacklisted
    session_result = await db.execute(
        select(AdminSession).where(
            and_(
                AdminSession.token_jti == jti,
                AdminSession.revoked_at.isnot(None)
            )
        )
    )
    if session_result.scalar_one_or_none():
        raise credentials_exception
    
    # Get user with roles
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(AdminUser)
        .where(AdminUser.id == user_id)
        .options(selectinload(AdminUser.roles))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_superuser(
    current_user: AdminUser = Depends(get_current_user)
) -> AdminUser:
    """Get current user if they are a superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


class PermissionChecker:
    """Dependency to check if user has required permissions"""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self, 
        current_user: AdminUser = Depends(get_current_user)
    ) -> AdminUser:
        if current_user.is_superuser:
            return current_user
            
        user_permissions = current_user.permissions
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
        
        return current_user


# Convenience functions for common permission checks
require_permission = PermissionChecker


async def create_session_record(
    db: AsyncSession,
    user: AdminUser,
    token_jti: str,
    request: Optional[Any] = None
) -> AdminSession:
    """Create a session record for tracking"""
    session = AdminSession(
        user_id=user.id,
        token_jti=token_jti,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    db.add(session)
    await db.commit()
    return session


async def revoke_token(db: AsyncSession, jti: str) -> None:
    """Revoke a token by its JTI"""
    result = await db.execute(
        select(AdminSession).where(AdminSession.token_jti == jti)
    )
    session = result.scalar_one_or_none()
    
    if session:
        session.revoked_at = datetime.utcnow()
        await db.commit()


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Clean up expired sessions - should be run periodically"""
    from sqlalchemy import delete
    
    result = await db.execute(
        delete(AdminSession).where(
            AdminSession.expires_at < datetime.utcnow()
        )
    )
    await db.commit()
    return result.rowcount