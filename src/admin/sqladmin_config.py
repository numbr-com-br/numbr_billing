from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.admin.auth import authenticate_user
from src.database import AsyncSessionLocal


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin"""

    async def login(self, request: Request) -> bool:
        """Handle admin login"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with AsyncSessionLocal() as db:
            user = await authenticate_user(db, username, password)
            if not user:
                return False

            # Store user info in session
            request.session.update({
                "user_id": user.id,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "permissions": list(user.permissions),
            })

        return True

    async def logout(self, request: Request) -> bool:
        """Handle logout"""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated"""
        user_id = request.session.get("user_id")

        if not user_id:
            return False

        return True


class SecureModelView(ModelView):
    """Base model view with permission checking"""

    # Override these in subclasses
    required_permissions = []

    def is_accessible(self, request: Request) -> bool:
        """Check if current user can access this view"""
        if not request.session.get("user_id"):
            return False

        # Superusers have all access
        if request.session.get("is_superuser"):
            return True

        # Check permissions
        user_permissions = set(request.session.get("permissions", []))
        required = set(self.required_permissions)

        return required.issubset(user_permissions)

    def is_visible(self, request: Request) -> bool:
        """Check if view should be visible in menu"""
        return self.is_accessible(request)

    def can_create(self, request: Request) -> bool:
        """Check if user can create new records"""
        if not self.is_accessible(request):
            return False

        # Check for WRITE permission
        required_write = [p.replace("_READ", "_WRITE") for p in self.required_permissions]
        user_permissions = set(request.session.get("permissions", []))

        return request.session.get("is_superuser") or any(
            p in user_permissions for p in required_write
        )

    def can_edit(self, request: Request) -> bool:
        """Check if user can edit records"""
        return self.can_create(request)

    def can_delete(self, request: Request) -> bool:
        """Check if user can delete records"""
        if not self.can_create(request):
            return False

        # Check for DELETE permission
        required_delete = [
            p.replace("_READ", "_DELETE").replace("_WRITE", "_DELETE")
            for p in self.required_permissions
        ]
        user_permissions = set(request.session.get("permissions", []))

        return request.session.get("is_superuser") or any(
            p in user_permissions for p in required_delete
        )