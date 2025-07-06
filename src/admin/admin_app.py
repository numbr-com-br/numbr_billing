from sqladmin import Admin
from src.admin.sqladmin_lambda import LambdaAdminAuthBackend
from src.admin.model_views import admin_views
from src.config import settings


def create_admin(app, engine):
    """Create and configure SQLAdmin instance"""
    # Initialize Lambda-compatible authentication backend
    authentication_backend = LambdaAdminAuthBackend(secret_key=settings.jwt_secret_key)

    # Create admin instance
    admin = Admin(
        app=app,
        engine=engine,
        title="Numbr Billing Admin",
        authentication_backend=authentication_backend,
        base_url="/admin",
    )

    # Register all model views
    for view in admin_views:
        admin.add_view(view)

    return admin
