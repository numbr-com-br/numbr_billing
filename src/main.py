from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from src.routers import checkout, webhooks
from src.routers.admin_auth import router as admin_auth_router
from src.routers.admin_users import router as admin_users_router
from src.routers.admin_roles import router as admin_roles_router
from src.database import engine, Base
from src.config import settings
from src.admin.admin_app import create_admin
from src.admin.cookie_middleware import AdminCookieMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Numbr Billing API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware (required for SQLAdmin)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="numbr_admin_session",
    max_age=86400,  # 24 hours
)

# Add cookie middleware for Lambda-compatible admin authentication
app.add_middleware(AdminCookieMiddleware)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

# Include routers
app.include_router(checkout.router)
app.include_router(webhooks.router)

# Include admin routers
app.include_router(admin_auth_router)
app.include_router(admin_users_router)
app.include_router(admin_roles_router)

# Initialize SQLAdmin
admin = create_admin(app, engine)

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )