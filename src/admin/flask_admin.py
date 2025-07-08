from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from typing import Optional
import os

from src.database import SessionLocal
from src.models.admin_user import AdminUser, AdminRole
from src.admin.permissions import Permission


class AuthenticatedModelView(ModelView):
    """Base model view with JWT authentication and RBAC support"""
    
    def __init__(self, model, session, required_permission: Optional[Permission] = None, **kwargs):
        self.required_permission = required_permission
        super().__init__(model, session, **kwargs)
    
    def is_accessible(self):
        """Check if current user has access to this view"""
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if not user_id:
                return False
            
            if not self.required_permission:
                return True
            
            db = SessionLocal()
            try:
                user = db.query(AdminUser).filter_by(id=user_id).first()
                if not user or not user.is_active:
                    return False
                
                return user.has_permission(self.required_permission)
            finally:
                db.close()
        except:
            return False
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page when access is denied"""
        return redirect(url_for('admin_auth.login', next=request.url))
    
    def on_model_change(self, form, model, is_created):
        """Hook for model changes - can be overridden in subclasses"""
        pass
    
    def on_model_delete(self, model):
        """Hook for model deletion - can be overridden in subclasses"""
        pass


class AuthenticatedAdminIndexView(AdminIndexView):
    """Custom index view with authentication"""
    
    def is_accessible(self):
        """Check if current user has access to admin panel"""
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            return user_id is not None
        except:
            return False
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login when access is denied"""
        return redirect(url_for('admin_auth.login', next=request.url))


class ReadOnlyModelView(AuthenticatedModelView):
    """Read-only model view for logs and payment records"""
    
    can_create = False
    can_edit = False
    can_delete = False
    can_export = True
    
    
class AdminUserView(AuthenticatedModelView):
    """Custom view for AdminUser model"""
    
    column_list = ['email', 'full_name', 'is_active', 'is_superuser', 'roles', 'created_at']
    column_searchable_list = ['email', 'full_name']
    column_filters = ['is_active', 'is_superuser', 'created_at']
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash', 'sessions', 'created_at', 'updated_at']
    
    def scaffold_form(self):
        form_class = super().scaffold_form()
        from wtforms import PasswordField
        from wtforms.validators import Optional
        form_class.password = PasswordField('Password', validators=[Optional()])
        return form_class
    
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        super().on_model_change(form, model, is_created)


class CustomerView(AuthenticatedModelView):
    """Custom view for Customer model"""
    
    column_list = ['name', 'email', 'cpf_cnpj', 'phone', 'annual_revenue', 'asaas_customer_id', 'created_at']
    column_searchable_list = ['name', 'email', 'cpf_cnpj', 'phone', 'asaas_customer_id']
    column_filters = ['created_at', 'annual_revenue']
    column_default_sort = ('created_at', True)
    

class PlanView(AuthenticatedModelView):
    """Custom view for Plan model"""
    
    column_list = ['name', 'description', 'cycle', 'is_active', 'created_at']
    column_searchable_list = ['name', 'description']
    column_filters = ['cycle', 'is_active', 'created_at']
    form_columns = ['name', 'description', 'cycle', 'is_active', 'features']
    

class SubscriptionView(AuthenticatedModelView):
    """Custom view for Subscription model"""
    
    column_list = ['customer', 'plan', 'status', 'next_due_date', 'created_at']
    column_searchable_list = ['asaas_subscription_id']
    column_filters = ['status', 'created_at', 'next_due_date']
    column_default_sort = ('created_at', True)
    

class PaymentView(ReadOnlyModelView):
    """Read-only view for Payment model"""
    
    column_list = ['subscription', 'amount', 'status', 'billing_type', 'due_date', 'paid_at', 'created_at']
    column_searchable_list = ['asaas_payment_id']
    column_filters = ['status', 'billing_type', 'created_at', 'due_date', 'paid_at']
    column_default_sort = ('created_at', True)
    

class WebhookLogView(ReadOnlyModelView):
    """Read-only view for WebhookLog model"""
    
    column_list = ['event', 'success', 'processed_at']
    column_searchable_list = ['event']
    column_filters = ['event', 'success', 'processed_at']
    column_default_sort = ('processed_at', True)
    can_view_details = True
    

def init_admin(app):
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    
    base_url = '/admin'
    if os.environ.get('IS_LAMBDA'):
        app.config['FLASK_ADMIN_USE_CDN'] = True
    
    admin = Admin(
        app,
        name='Numbr Billing Admin',
        template_mode='bootstrap4',
        index_view=AuthenticatedAdminIndexView()
    )
    
    db_session = SessionLocal()
    
    from src.models.customer import Customer
    from src.models.plan import Plan
    from src.models.addon import Addon
    from src.models.subscription import Subscription, SubscriptionAddon
    from src.models.payment import Payment
    from src.models.webhook_log import WebhookLog
    from src.models.revenue_range import RevenueRange
    from src.models.plan_pricing import PlanPricing
    
    admin.add_view(AdminUserView(
        AdminUser, db_session,
        name='Users',
        category='Admin',
        required_permission=Permission.ADMIN_USERS_READ
    ))
    
    admin.add_view(AuthenticatedModelView(
        AdminRole, db_session,
        name='Roles',
        category='Admin',
        required_permission=Permission.ADMIN_ROLES_READ
    ))
    
    admin.add_view(CustomerView(
        Customer, db_session,
        name='Customers',
        category='Customers',
        required_permission=Permission.CUSTOMERS_READ
    ))
    
    admin.add_view(PlanView(
        Plan, db_session,
        name='Plans',
        category='Billing',
        required_permission=Permission.PLANS_READ
    ))
    
    admin.add_view(AuthenticatedModelView(
        Addon, db_session,
        name='Addons',
        category='Billing',
        required_permission=Permission.ADDONS_READ
    ))
    
    admin.add_view(AuthenticatedModelView(
        RevenueRange, db_session,
        name='Revenue Ranges',
        category='Billing',
        required_permission=Permission.PLANS_READ
    ))
    
    admin.add_view(AuthenticatedModelView(
        PlanPricing, db_session,
        name='Plan Pricing',
        category='Billing',
        required_permission=Permission.PLANS_READ
    ))
    
    admin.add_view(SubscriptionView(
        Subscription, db_session,
        name='Subscriptions',
        category='Subscriptions',
        required_permission=Permission.SUBSCRIPTIONS_READ
    ))
    
    admin.add_view(AuthenticatedModelView(
        SubscriptionAddon, db_session,
        name='Subscription Addons',
        category='Subscriptions',
        required_permission=Permission.SUBSCRIPTIONS_READ
    ))
    
    admin.add_view(PaymentView(
        Payment, db_session,
        name='Payments',
        category='Reports',
        required_permission=Permission.PAYMENTS_READ
    ))
    
    admin.add_view(WebhookLogView(
        WebhookLog, db_session,
        name='Webhook Logs',
        category='Reports',
        required_permission=Permission.WEBHOOKS_READ
    ))
    
    @app.teardown_appcontext
    def close_admin_session(error):
        if hasattr(app, '_admin_db_session'):
            app._admin_db_session.close()
    
    app._admin_db_session = db_session
    
    return admin