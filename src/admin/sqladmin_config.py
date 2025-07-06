from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from jose import jwt, JWTError
from datetime import datetime, timedelta
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
COOKIE_SECURE = settings.environment not in ["dev", "stg", "staging", "development", "local"]  # Only HTTPS in production
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"
COOKIE_MAX_AGE = 60 * ACCESS_TOKEN_EXPIRE_MINUTES  # Same as token expiration


class AdminAuthBackend(AuthenticationBackend):
    """Custom authentication backend for SQLAdmin - Lambda compatible"""
    
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
            
            # Create access token
            access_token_data = {
                "sub": user.id,
                "email": user.email,
                "type": "access",
                "roles": [role.name for role in user.roles],
                "permissions": list(user.permissions),
                "is_superuser": user.is_superuser
            }
            
            # Create tokens with JTI
            access_token = create_access_token(access_token_data)
            
            # Extract JTI from the created token for session tracking
            token_payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            token_jti = token_payload.get("jti")
            
            # Create session record in database
            await create_session_record(db, user, token_jti, request)
            await db.commit()
            
            # Store token in cookie (Lambda compatible)
            response = request.state.response = Response()
            response.set_cookie(
                key=COOKIE_NAME,
                value=access_token,
                max_age=COOKIE_MAX_AGE,
                secure=COOKIE_SECURE,
                httponly=COOKIE_HTTPONLY,
                samesite=COOKIE_SAMESITE
            )
            
            return True
    
    async def logout(self, request: Request) -> bool:
        """Handle logout process"""
        # Get token from cookie
        token = request.cookies.get(COOKIE_NAME)
        
        if token:
            try:
                # Decode token to get JTI
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
                jti = payload.get("jti")
                
                if jti:
                    # Revoke token in database
                    async with AsyncSessionLocal() as db:
                        await revoke_token(db, jti)
                        await db.commit()
            except:
                pass
        
        # Clear cookie
        response = request.state.response = Response()
        response.delete_cookie(
            key=COOKIE_NAME,
            secure=COOKIE_SECURE,
            httponly=COOKIE_HTTPONLY,
            samesite=COOKIE_SAMESITE
        )
        
        return True
    
    async def authenticate(self, request: Request) -> Optional[RedirectResponse]:
        """Check if user is authenticated"""
        token = request.cookies.get(COOKIE_NAME)
        
        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        
        try:
            # Verify token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check expiration (JWT handles this automatically, but being explicit)
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return RedirectResponse(request.url_for("admin:login"), status_code=302)
            
            # Store user info in request state for use in views
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.is_superuser = payload.get("is_superuser", False)
            request.state.permissions = payload.get("permissions", [])
            
            return None
            
        except JWTError:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)


class SecureModelView(ModelView):
    """Base model view with permission checking"""
    
    # Override these in subclasses
    required_permissions = []
    
    def is_accessible(self, request: Request) -> bool:
        """Check if current user can access this view"""
        # Check if user is authenticated (has valid token in cookie)
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return False
        
        try:
            # Decode and validate token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return False
            
            # Superusers have all access
            if payload.get("is_superuser"):
                return True
            
            # Check required permissions
            user_permissions = set(payload.get("permissions", []))
            required = set(self.required_permissions)
            
            return required.issubset(user_permissions)
            
        except JWTError:
            return False
    
    def is_visible(self, request: Request) -> bool:
        """Check if view should be visible in menu"""
        return self.is_accessible(request)
    
    def can_create(self, request: Request) -> bool:
        """Check if user can create new records"""
        if not self.is_accessible(request):
            return False
        
        # Check for WRITE permission
        required_write = [p.replace("_READ", "_WRITE") for p in self.required_permissions]
        
        try:
            token = request.cookies.get(COOKIE_NAME)
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("is_superuser"):
                return True
            
            user_permissions = set(payload.get("permissions", []))
            return any(p in user_permissions for p in required_write)
            
        except:
            return False
    
    def can_edit(self, request: Request) -> bool:
        """Check if user can edit records"""
        return self.can_create(request)
    
    def can_delete(self, request: Request) -> bool:
        """Check if user can delete records"""
        if not self.can_create(request):
            return False
        
        # Check for DELETE permission
        required_delete = [p.replace("_READ", "_DELETE").replace("_WRITE", "_DELETE") 
                          for p in self.required_permissions]
        
        try:
            token = request.cookies.get(COOKIE_NAME)
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("is_superuser"):
                return True
            
            user_permissions = set(payload.get("permissions", []))
            return any(p in user_permissions for p in required_delete)
            
        except:
            return False