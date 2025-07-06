"""
SQLAdmin authentication backend optimized for AWS Lambda
Uses JWT tokens stored in cookies for stateless authentication
"""
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
    create_session_record, revoke_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.database import AsyncSessionLocal
from src.config import settings


# Cookie settings for Lambda compatibility
COOKIE_NAME = "numbr_admin_token"
# Only use secure cookies in production
COOKIE_SECURE = settings.environment not in ["dev", "stg", "staging", "development", "local"]
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
COOKIE_DOMAIN = None  # Let browser handle domain
COOKIE_PATH = "/admin"  # Restrict to admin routes


class LambdaAdminAuthBackend(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin that works in AWS Lambda.
    Uses JWT tokens in cookies instead of server-side sessions.
    """
    
    async def login(self, request: Request) -> bool:
        """Handle admin login and set JWT cookie"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        if not username or not password:
            return False
        
        async with AsyncSessionLocal() as db:
            user = await authenticate_user(db, username, password)
            if not user:
                return False
            
            # Create access token with user data
            access_token_data = {
                "sub": user.id,
                "email": user.email,
                "type": "access",
                "roles": [role.name for role in user.roles],
                "permissions": list(user.permissions),
                "is_superuser": user.is_superuser
            }
            
            # Create token (JTI is added inside create_access_token)
            access_token = create_access_token(access_token_data)
            
            # Extract JTI for session tracking
            token_payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            token_jti = token_payload.get("jti")
            
            # Track session in database
            await create_session_record(db, user, token_jti, request)
            await db.commit()
            
            # Set cookie in request (SQLAdmin will handle the response)
            # Use a custom attribute to pass the token to the response
            request.state._admin_token = access_token
            
            return True
    
    async def logout(self, request: Request) -> bool:
        """Handle logout and clear JWT cookie"""
        token = request.cookies.get(COOKIE_NAME)
        
        if token:
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
                jti = payload.get("jti")
                
                if jti:
                    async with AsyncSessionLocal() as db:
                        await revoke_token(db, jti)
                        await db.commit()
            except:
                pass  # Token might be invalid, continue with logout
        
        # Mark for cookie deletion
        request.state._clear_admin_token = True
        return True
    
    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Verify JWT token from cookie"""
        token = request.cookies.get(COOKIE_NAME)
        
        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        
        try:
            # Verify and decode token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            # Store user info in request for access in views
            request.state.admin_user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "is_superuser": payload.get("is_superuser", False),
                "permissions": payload.get("permissions", []),
                "roles": payload.get("roles", [])
            }
            
            return None
            
        except JWTError:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)


class LambdaSecureModelView(ModelView):
    """Base model view with JWT-based permission checking"""
    
    # Override in subclasses
    required_permissions = []
    
    def _get_user_from_request(self, request: Request) -> Optional[dict]:
        """Extract user info from JWT token"""
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return None
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "is_superuser": payload.get("is_superuser", False),
                "permissions": payload.get("permissions", []),
                "roles": payload.get("roles", [])
            }
        except JWTError:
            return None
    
    def is_accessible(self, request: Request) -> bool:
        """Check if current user can access this view"""
        user = self._get_user_from_request(request)
        if not user:
            return False
        
        # Superusers have all access
        if user.get("is_superuser"):
            return True
        
        # Check required permissions
        user_permissions = set(user.get("permissions", []))
        required = set(self.required_permissions)
        
        return required.issubset(user_permissions)
    
    def is_visible(self, request: Request) -> bool:
        """Check if view should be visible in menu"""
        return self.is_accessible(request)
    
    def can_create(self, request: Request) -> bool:
        """Check if user can create new records"""
        user = self._get_user_from_request(request)
        if not user:
            return False
        
        if user.get("is_superuser"):
            return True
        
        # Check for WRITE permission
        required_write = [p.replace("_READ", "_WRITE") for p in self.required_permissions]
        user_permissions = set(user.get("permissions", []))
        
        return any(p in user_permissions for p in required_write)
    
    def can_edit(self, request: Request) -> bool:
        """Check if user can edit records"""
        return self.can_create(request)
    
    def can_delete(self, request: Request) -> bool:
        """Check if user can delete records"""
        user = self._get_user_from_request(request)
        if not user:
            return False
        
        if user.get("is_superuser"):
            return True
        
        # Check for DELETE permission
        required_delete = [p.replace("_READ", "_DELETE").replace("_WRITE", "_DELETE") 
                          for p in self.required_permissions]
        user_permissions = set(user.get("permissions", []))
        
        return any(p in user_permissions for p in required_delete)