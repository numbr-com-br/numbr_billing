from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, exists
from typing import List, Optional
from datetime import datetime

from src.database import get_db as get_session
from src.models.admin_user import AdminRole, AdminUser, admin_user_roles
from src.schemas.admin_auth import AdminRoleCreate, AdminRoleUpdate, AdminRoleResponse
from src.admin.auth import require_permission
from src.admin.permissions import Permission, PERMISSION_DESCRIPTIONS, get_permission_groups

router = APIRouter(prefix="/api/admin/roles", tags=["Admin Roles"])


@router.get("", response_model=List[AdminRoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_READ])),
    db: AsyncSession = Depends(get_session),
):
    """List all roles with pagination"""
    query = select(AdminRole)

    # Apply search filter
    if search:
        query = query.where(
            or_(AdminRole.name.ilike(f"%{search}%"), AdminRole.description.ilike(f"%{search}%"))
        )

    # Get total count (TODO: return in response for pagination)
    # count_query = select(func.count()).select_from(query.subquery())
    # total_result = await db.execute(count_query)
    # total = total_result.scalar()

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(AdminRole.created_at.desc())

    result = await db.execute(query)
    roles = result.scalars().all()

    # Get user count for each role
    role_responses = []
    for role in roles:
        user_count_result = await db.execute(
            select(func.count())
            .select_from(admin_user_roles)
            .where(admin_user_roles.c.role_id == role.id)
        )
        user_count = user_count_result.scalar()

        role_responses.append(
            AdminRoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                permissions=role.permissions,
                is_system=role.is_system,
                created_at=role.created_at,
                updated_at=role.updated_at,
                user_count=user_count,
            )
        )

    return role_responses


@router.get("/permissions")
async def get_available_permissions(
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_READ])),
):
    """Get all available permissions grouped by resource"""
    permission_groups = get_permission_groups()

    # Convert enum values to strings with descriptions
    result = {}
    for group_name, permissions in permission_groups.items():
        result[group_name] = [
            {"value": perm.value, "description": PERMISSION_DESCRIPTIONS.get(perm, perm.value)}
            for perm in permissions
        ]

    return result


@router.get("/{role_id}", response_model=AdminRoleResponse)
async def get_role(
    role_id: str,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_READ])),
    db: AsyncSession = Depends(get_session),
):
    """Get a specific role by ID"""
    result = await db.execute(select(AdminRole).where(AdminRole.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Get user count
    user_count_result = await db.execute(
        select(func.count())
        .select_from(admin_user_roles)
        .where(admin_user_roles.c.role_id == role.id)
    )
    user_count = user_count_result.scalar()

    return AdminRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        user_count=user_count,
    )


@router.post("", response_model=AdminRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: AdminRoleCreate,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_WRITE])),
    db: AsyncSession = Depends(get_session),
):
    """Create a new role"""
    # Check if role name already exists
    existing_role = await db.execute(select(AdminRole).where(AdminRole.name == role_data.name))
    if existing_role.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role name already exists"
        )

    # Validate permissions
    valid_permissions = [p.value for p in Permission]
    invalid_permissions = [p for p in role_data.permissions if p not in valid_permissions]

    if invalid_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions: {', '.join(invalid_permissions)}",
        )

    # Create role
    new_role = AdminRole(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        is_system=False,  # User-created roles are not system roles
    )

    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)

    return AdminRoleResponse(
        id=new_role.id,
        name=new_role.name,
        description=new_role.description,
        permissions=new_role.permissions,
        is_system=new_role.is_system,
        created_at=new_role.created_at,
        updated_at=new_role.updated_at,
        user_count=0,
    )


@router.put("/{role_id}", response_model=AdminRoleResponse)
async def update_role(
    role_id: str,
    role_data: AdminRoleUpdate,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_WRITE])),
    db: AsyncSession = Depends(get_session),
):
    """Update a role"""
    result = await db.execute(select(AdminRole).where(AdminRole.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Cannot modify system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify system roles"
        )

    # Check if new name already exists
    if role_data.name and role_data.name != role.name:
        existing_role = await db.execute(select(AdminRole).where(AdminRole.name == role_data.name))
        if existing_role.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Role name already exists"
            )

    # Validate permissions if provided
    if role_data.permissions is not None:
        valid_permissions = [p.value for p in Permission]
        invalid_permissions = [p for p in role_data.permissions if p not in valid_permissions]

        if invalid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permissions: {', '.join(invalid_permissions)}",
            )

    # Update fields
    update_data = role_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    role.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(role)

    # Get user count
    user_count_result = await db.execute(
        select(func.count())
        .select_from(admin_user_roles)
        .where(admin_user_roles.c.role_id == role.id)
    )
    user_count = user_count_result.scalar()

    return AdminRoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at,
        user_count=user_count,
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_WRITE])),
    db: AsyncSession = Depends(get_session),
):
    """Delete a role"""
    result = await db.execute(select(AdminRole).where(AdminRole.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Cannot delete system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete system roles"
        )

    # Check if role is assigned to any users
    user_count_result = await db.execute(
        select(func.count())
        .select_from(admin_user_roles)
        .where(admin_user_roles.c.role_id == role.id)
    )
    user_count = user_count_result.scalar()

    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role assigned to {user_count} user(s)",
        )

    await db.delete(role)
    await db.commit()

    return {"message": "Role deleted successfully"}


@router.get("/{role_id}/users", response_model=List[dict])
async def get_role_users(
    role_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AdminUser = Depends(require_permission([Permission.ADMIN_ROLES_READ])),
    db: AsyncSession = Depends(get_session),
):
    """Get all users assigned to a role"""
    # Check if role exists
    role_exists = await db.execute(select(exists().where(AdminRole.id == role_id)))
    if not role_exists.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Get users with this role
    query = (
        select(AdminUser)
        .join(AdminUser.roles)
        .where(AdminRole.id == role_id)
        .offset(skip)
        .limit(limit)
        .order_by(AdminUser.created_at.desc())
    )

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
        }
        for user in users
    ]
