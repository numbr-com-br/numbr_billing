from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from jose import jwt, JWTError
from datetime import datetime
from typing import Optional

from src.admin.auth import (
    JWT_SECRET_KEY, ALGORITHM, authenticate_user,
    create_access_token, create_refresh_token, 
    create_session_record
)
from src.database import AsyncSessionLocal
from src.models.admin_user import AdminUser


class AdminAuthBackend(AuthenticationBackend):
    """Custom authentication backend for SQLAdmin"""
    
    async def login(self, request: Request) -> bool:
        """Handle login process"""
        form = await request.form()
        email = form.get("username")  # SQLAdmin uses "username" field
        password = form.get("password")
        
        if not email or not password:
            return False
        
        async with AsyncSessionLocal() as db:
            user = await authenticate_user(db, email, password)
            
            if not user:
                return False
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            # Create tokens
            access_token_data = {
                "sub": user.id,
                "email": user.email,
                "type": "access",
                "roles": [role.name for role in user.roles],
                "permissions": list(user.permissions)
            }
            
            access_token = create_access_token(access_token_data)
            refresh_token = create_refresh_token(user.id)
            
            # Create session record
            token_jti = access_token_data.get("jti")
            await create_session_record(db, user, token_jti, request)
            
            await db.commit()
            
            # Store in session
            request.session.update({
                "token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "permissions": list(user.permissions)
            })
            
            return True
    
    async def logout(self, request: Request) -> bool:
        """Handle logout process"""
        # Clear session
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Check if user is authenticated"""
        token = request.session.get("token")
        
        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        
        try:
            # Verify token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                request.session.clear()
                return RedirectResponse(request.url_for("admin:login"), status_code=302)
            
            return None
            
        except JWTError:
            request.session.clear()
            return RedirectResponse(request.url_for("admin:login"), status_code=302)


class SecureModelView(ModelView):
    """Base model view with permission checking"""
    
    # Override these in subclasses
    required_permissions = []
    
    def is_accessible(self, request: Request) -> bool:
        """Check if current user can access this view"""
        if not request.session.get("token"):
            return False
        
        # Superusers have all access
        if request.session.get("is_superuser"):
            return True
        
        # Check required permissions
        user_permissions = set(request.session.get("permissions", []))
        required = set(self.required_permissions)
        
        return required.issubset(user_permissions)
    
    def is_visible(self, request: Request) -> bool:
        """Check if this view should be visible in menu"""
        return self.is_accessible(request)
    
    # Permission-based field/action control
    def can_create(self, request: Request) -> bool:
        """Check if user can create records"""
        if not self.is_accessible(request):
            return False
        
        if request.session.get("is_superuser"):
            return True
        
        # Check for write permission
        user_permissions = request.session.get("permissions", [])
        resource = self.model.__tablename__
        write_permission = f"{resource}:write"
        
        return write_permission in user_permissions
    
    def can_edit(self, request: Request) -> bool:
        """Check if user can edit records"""
        return self.can_create(request)
    
    def can_delete(self, request: Request) -> bool:
        """Check if user can delete records"""
        if not self.is_accessible(request):
            return False
        
        if request.session.get("is_superuser"):
            return True
        
        # Check for delete permission
        user_permissions = request.session.get("permissions", [])
        resource = self.model.__tablename__
        delete_permission = f"{resource}:delete"
        
        return delete_permission in user_permissions
    
    def can_view_details(self, request: Request) -> bool:
        """Check if user can view record details"""
        return self.is_accessible(request)


def create_admin_app(app, engine, session_secret_key: str):
    """Create and configure SQLAdmin instance"""
    authentication_backend = AdminAuthBackend(secret_key=session_secret_key)
    
    admin = Admin(
        app=app,
        engine=engine,
        title="Numbr Billing Admin",
        authentication_backend=authentication_backend,
        templates_dir="src/admin/templates",  # Custom templates if needed
    )
    
    return admin