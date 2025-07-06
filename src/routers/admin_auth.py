from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import List, Optional, Annotated

from src.database import get_db as get_session
from src.models.admin_user import AdminUser, AdminSession
from src.schemas.admin_auth import (
    LoginRequest,
    AdminUserResponse,
    ChangePasswordRequest,
    SessionResponse,
)
from src.admin.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Authentication"])
security = HTTPBearer()


async def create_session_record_with_info(
    db: AsyncSession,
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
    await db.commit()
    return session


@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_session),
    x_forwarded_for: Optional[str] = Header(None),
    x_real_ip: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
):
    """Login endpoint for admin users"""
    user = await authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    await db.execute(
        update(AdminUser).where(AdminUser.id == user.id).values(last_login=datetime.utcnow())
    )

    # Create tokens
    access_token_data = {
        "sub": user.id,
        "email": user.email,
        "type": "access",
        "roles": [role.name for role in user.roles],
        "permissions": list(user.permissions),
    }

    access_token = create_access_token(access_token_data)
    refresh_token = create_refresh_token(user.id)

    # Extract JTI from the generated token
    from jose import jwt
    from src.admin.auth import JWT_SECRET_KEY, ALGORITHM

    token_payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    token_jti = token_payload.get("jti")

    # Create session record with IP info
    client_ip = x_forwarded_for or x_real_ip or "unknown"
    await create_session_record_with_info(db, user, token_jti, client_ip, user_agent)

    await db.commit()

    # Create response with cookie
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="admin_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Use HTTPS in production
        samesite="strict",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return response


@router.post("/refresh")
async def refresh_token(
    db: AsyncSession = Depends(get_session),
    admin_refresh_token: Annotated[Optional[str], Cookie()] = None,
    x_forwarded_for: Optional[str] = Header(None),
    x_real_ip: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
):
    """Refresh access token using refresh token from cookie"""
    if not admin_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    try:
        from jose import jwt
        from src.admin.auth import JWT_SECRET_KEY, ALGORITHM

        payload = jwt.decode(admin_refresh_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user
        result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Create new access token
        access_token_data = {
            "sub": user.id,
            "email": user.email,
            "type": "access",
            "roles": [role.name for role in user.roles],
            "permissions": list(user.permissions),
        }

        access_token = create_access_token(access_token_data)
        new_refresh_token = create_refresh_token(user.id)

        # Extract JTI from the generated token
        token_payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_jti = token_payload.get("jti")

        # Create session record with IP info
        client_ip = x_forwarded_for or x_real_ip or "unknown"
        await create_session_record_with_info(db, user, token_jti, client_ip, user_agent)
        await db.commit()

        # Create response with new refresh token cookie
        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }
        )

        # Update refresh token cookie
        response.set_cookie(
            key="admin_refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )

        return response

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.post("/logout", response_model=None)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Logout current user"""
    # Get token from credentials
    try:
        from jose import jwt
        from src.admin.auth import JWT_SECRET_KEY, ALGORITHM, revoke_token

        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        if jti:
            await revoke_token(db, jti)
    except Exception:
        pass

    # Create response and delete refresh token cookie
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="admin_refresh_token")

    return response


@router.get("/me", response_model=AdminUserResponse)
async def get_current_user_info(current_user: AdminUser = Depends(get_current_user)):
    """Get current user information"""
    return AdminUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        roles=[
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            }
            for role in current_user.roles
        ],
        permissions=list(current_user.permissions),
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Change current user's password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )

    # Check if new password is different
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    new_password_hash = get_password_hash(password_data.new_password)
    await db.execute(
        update(AdminUser)
        .where(AdminUser.id == current_user.id)
        .values(password_hash=new_password_hash, updated_at=datetime.utcnow())
    )

    # Revoke all sessions except current
    # This forces re-login on all other devices
    from jose import jwt
    from src.admin.auth import JWT_SECRET_KEY, ALGORITHM

    current_jti = None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        current_jti = payload.get("jti")
    except Exception:
        pass

    if current_jti:
        await db.execute(
            update(AdminSession)
            .where(
                AdminSession.user_id == current_user.id,
                AdminSession.token_jti != current_jti,
                AdminSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )

    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get all active sessions for current user"""
    result = await db.execute(
        select(AdminSession)
        .where(
            AdminSession.user_id == current_user.id,
            AdminSession.revoked_at.is_(None),
            AdminSession.expires_at > datetime.utcnow(),
        )
        .order_by(AdminSession.created_at.desc())
    )
    sessions = result.scalars().all()

    # Get current session JTI from the provided credentials
    current_jti = None
    try:
        from jose import jwt
        from src.admin.auth import JWT_SECRET_KEY, ALGORITHM

        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        current_jti = payload.get("jti")
    except Exception:
        pass

    return [
        SessionResponse(
            id=session.id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_current=session.token_jti == current_jti,
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Revoke a specific session"""
    result = await db.execute(
        select(AdminSession).where(
            AdminSession.id == session_id, AdminSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.revoked_at = datetime.utcnow()
    await db.commit()

    return {"message": "Session revoked successfully"}
