from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
import uuid

# Association table for many-to-many relationship
admin_user_roles = Table(
    "admin_user_roles",
    Base.metadata,
    Column(
        "user_id", String(36), ForeignKey("admin_users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", String(36), ForeignKey("admin_roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("assigned_at", DateTime, server_default=func.now()),
    Column("assigned_by", String(36), ForeignKey("admin_users.id"), nullable=True),
)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    roles = relationship(
        "AdminRole",
        secondary=admin_user_roles,
        back_populates="users",
        primaryjoin="AdminUser.id == admin_user_roles.c.user_id",
        secondaryjoin="AdminRole.id == admin_user_roles.c.role_id",
    )
    sessions = relationship("AdminSession", back_populates="user", cascade="all, delete-orphan")

    @property
    def permissions(self) -> set:
        """Get all permissions from all roles"""
        perms = set()
        for role in self.roles:
            if role.permissions:
                perms.update(role.permissions)
        return perms

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        return permission in self.permissions


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    permissions = Column(JSON, nullable=False, default=list)
    is_system = Column(Boolean, nullable=False, default=False)  # System roles can't be deleted
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship(
        "AdminUser",
        secondary=admin_user_roles,
        back_populates="roles",
        primaryjoin="AdminRole.id == admin_user_roles.c.role_id",
        secondaryjoin="AdminUser.id == admin_user_roles.c.user_id",
    )


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False)
    token_jti = Column(String(36), unique=True, nullable=False)  # JWT ID for blacklisting
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)  # For manual revocation
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("AdminUser", back_populates="sessions")

    @property
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        from datetime import datetime

        now = datetime.utcnow()
        return self.revoked_at is None and self.expires_at > now
