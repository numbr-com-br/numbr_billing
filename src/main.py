from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
import os

from src.routers import checkout, webhooks
from src.routers.admin_auth import create_admin_auth_blueprint
from src.routers.admin_users import create_admin_users_blueprint
from src.routers.admin_roles import create_admin_roles_blueprint
from src.database import engine, Base, get_db, close_db_session
from src.config import settings
from src.admin.flask_admin import init_admin


def create_app():
    app = Flask(__name__, template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = settings.jwt_secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = settings.jwt_secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Enable in production
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Configure CORS
    CORS(app, origins=["*"], allow_headers=["*"], methods=["*"])
    
    # Context processor to inject current user in templates
    @app.context_processor
    def inject_user():
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                from src.database import SessionLocal
                from src.models.admin_user import AdminUser
                db = SessionLocal()
                try:
                    user = db.query(AdminUser).filter_by(id=user_id).first()
                    return dict(current_user=user)
                finally:
                    db.close()
        except:
            pass
        return dict(current_user=None)
    
    # Health check
    @app.route('/health')
    def health_check():
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    # Register blueprints
    app.register_blueprint(checkout.create_checkout_blueprint(), url_prefix="/api/checkout")
    app.register_blueprint(webhooks.create_webhook_blueprint(), url_prefix="/webhooks")
    
    # Register admin blueprints
    app.register_blueprint(create_admin_auth_blueprint(), url_prefix="/api/admin/auth")
    app.register_blueprint(create_admin_users_blueprint(), url_prefix="/api/admin/users")
    app.register_blueprint(create_admin_roles_blueprint(), url_prefix="/api/admin/roles")
    
    # Initialize Flask-Admin
    init_admin(app)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    # Create tables on startup
    with app.app_context():
        Base.metadata.create_all(bind=engine)
    
    # Register teardown handler
    app.teardown_appcontext(close_db_session)
    
    return app


# Create the Flask app
app = create_app()


# Run with development server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.port, debug=True)