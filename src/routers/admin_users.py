from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime

from src.database import get_db as get_session
from src.models.admin_user import AdminUser, AdminRole, admin_user_roles
from src.schemas.admin_auth import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    AdminRoleResponse
)
from src.admin.auth import (
    get_current_user, get_current_active_superuser,
    get_password_hash, require_permission
)
from src.admin.permissions import Permission

router = APIRouter(prefix="/api/admin/users", tags=["Admin Users"])


@router.get("", response_model=List[AdminUserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    role_id: Optional[str] = None,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_USERS_READ])),
    db: AsyncSession = Depends(get_session)
):
    """List all admin users with filtering and pagination"""
    query = select(AdminUser)
    
    # Apply filters
    filters = []
    if search:
        filters.append(
            or_(
                AdminUser.email.ilike(f"%{search}%"),
                AdminUser.full_name.ilike(f"%{search}%")
            )
        )
    
    if is_active is not None:
        filters.append(AdminUser.is_active == is_active)
    
    if role_id:
        query = query.join(AdminUser.roles).where(AdminRole.id == role_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(AdminUser.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[{
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "updated_at": role.updated_at
            } for role in user.roles],
            permissions=list(user.permissions)
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_USERS_READ])),
    db: AsyncSession = Depends(get_session)
):
    """Get a specific admin user by ID"""
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[{
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        } for role in user.roles],
        permissions=list(user.permissions)
    )


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_USERS_WRITE])),
    db: AsyncSession = Depends(get_session)
):
    """Create a new admin user"""
    # Check if email already exists
    existing_user = await db.execute(
        select(AdminUser).where(AdminUser.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Only superusers can create other superusers
    if user_data.is_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create other superusers"
        )
    
    # Create user
    new_user = AdminUser(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    
    # Add roles
    if user_data.role_ids:
        roles_result = await db.execute(
            select(AdminRole).where(AdminRole.id.in_(user_data.role_ids))
        )
        roles = roles_result.scalars().all()
        new_user.roles = roles
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return AdminUserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        roles=[{
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        } for role in new_user.roles],
        permissions=list(new_user.permissions)
    )


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    user_data: AdminUserUpdate,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_USERS_WRITE])),
    db: AsyncSession = Depends(get_session)
):
    """Update an admin user"""
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if trying to modify a superuser without being one
    if user.is_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can modify other superusers"
        )
    
    # Check if email is being changed and already exists
    if user_data.email and user_data.email != user.email:
        existing_user = await db.execute(
            select(AdminUser).where(AdminUser.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    if "role_ids" in update_data:
        role_ids = update_data.pop("role_ids")
        if role_ids is not None:
            roles_result = await db.execute(
                select(AdminRole).where(AdminRole.id.in_(role_ids))
            )
            user.roles = roles_result.scalars().all()
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[{
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        } for role in user.roles],
        permissions=list(user.permissions)
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: AdminUser = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_session)
):
    """Delete an admin user (superuser only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if this is the last superuser
    if user.is_superuser:
        superuser_count = await db.execute(
            select(func.count()).where(
                AdminUser.is_superuser == True,
                AdminUser.id != user_id
            )
        )
        if superuser_count.scalar() == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last superuser"
            )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}