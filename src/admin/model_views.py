from src.admin.sqladmin_lambda import LambdaSecureModelView as SecureModelView
from src.admin.permissions import Permission
from src.models import (
    Customer, Plan, Addon, Subscription, Payment, WebhookLog, AdminUser, AdminRole, RevenueRange, PlanPricing
)


class CustomerAdmin(SecureModelView, model=Customer):
    """Customer admin view"""
    name = "Customer"
    name_plural = "Customers"
    icon = "fa-solid fa-users"
    
    required_permissions = [Permission.CUSTOMERS_READ]
    
    # Column display configuration
    column_list = [
        Customer.id,
        Customer.email,
        Customer.name,
        Customer.cpf_cnpj,
        Customer.asaas_customer_id,
        Customer.created_at
    ]
    column_searchable_list = [Customer.email, Customer.name, Customer.cpf_cnpj]
    column_sortable_list = [Customer.created_at, Customer.name, Customer.email]
    column_default_sort = [(Customer.created_at, True)]  # Desc
    
    # Form configuration
    form_excluded_columns = [Customer.subscriptions]
    
    # Details view
    column_details_list = [
        Customer.id,
        Customer.asaas_customer_id,
        Customer.email,
        Customer.name,
        Customer.cpf_cnpj,
        Customer.phone,
        Customer.created_at,
        Customer.updated_at
    ]


class PlanAdmin(SecureModelView, model=Plan):
    """Plan admin view"""
    name = "Plan"
    name_plural = "Plans"
    icon = "fa-solid fa-clipboard-list"
    
    required_permissions = [Permission.PLANS_READ]
    
    column_list = [
        Plan.id,
        Plan.name,
        Plan.cycle,
        Plan.is_active,
        Plan.created_at
    ]
    column_searchable_list = [Plan.name]
    column_sortable_list = [Plan.name, Plan.created_at]
    column_default_sort = [(Plan.created_at, True)]
    
    form_excluded_columns = [Plan.subscriptions, Plan.plan_pricings]
    
    # Custom form configuration for JSON field
    form_args = {
        'features': {
            'label': 'Features (JSON)',
            'description': 'Enter features as a JSON array'
        }
    }


class AddonAdmin(SecureModelView, model=Addon):
    """Addon admin view"""
    name = "Addon"
    name_plural = "Addons"
    icon = "fa-solid fa-puzzle-piece"
    
    required_permissions = [Permission.ADDONS_READ]
    
    column_list = [
        Addon.id,
        Addon.name,
        Addon.price,
        Addon.type,
        Addon.is_active,
        Addon.created_at
    ]
    column_searchable_list = [Addon.name]
    column_filters = [Addon.type, Addon.is_active]
    column_sortable_list = [Addon.name, Addon.price, Addon.created_at]
    column_default_sort = [(Addon.created_at, True)]
    
    form_excluded_columns = [Addon.subscription_addons]


class SubscriptionAdmin(SecureModelView, model=Subscription):
    """Subscription admin view"""
    name = "Subscription"
    name_plural = "Subscriptions"
    icon = "fa-solid fa-credit-card"
    
    required_permissions = [Permission.SUBSCRIPTIONS_READ]
    
    column_list = [
        Subscription.id,
        Subscription.customer,
        Subscription.plan,
        Subscription.status,
        Subscription.next_due_date,
        Subscription.created_at
    ]
    column_searchable_list = [Subscription.asaas_subscription_id]
    column_filters = [Subscription.status, Subscription.plan]
    column_sortable_list = [Subscription.created_at, Subscription.next_due_date]
    column_default_sort = [(Subscription.created_at, True)]
    
    form_excluded_columns = [Subscription.payments, Subscription.addons]
    
    # Read-only fields
    form_widget_args = {
        'asaas_subscription_id': {'readonly': True},
        'customer': {'readonly': True},
        'plan': {'readonly': True}
    }


class PaymentAdmin(SecureModelView, model=Payment):
    """Payment admin view"""
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-money-bill"
    
    required_permissions = [Permission.PAYMENTS_READ]
    
    column_list = [
        Payment.id,
        Payment.subscription,
        Payment.amount,
        Payment.status,
        Payment.billing_type,
        Payment.due_date,
        Payment.created_at
    ]
    column_searchable_list = [Payment.asaas_payment_id]
    column_filters = [Payment.status, Payment.billing_type]
    column_sortable_list = [Payment.created_at, Payment.due_date, Payment.amount]
    column_default_sort = [(Payment.created_at, True)]
    
    # Most fields are read-only
    can_create = False  # Payments are created via API
    can_edit = False    # Payments shouldn't be edited manually
    can_delete = False  # Payments shouldn't be deleted


class WebhookLogAdmin(SecureModelView, model=WebhookLog):
    """Webhook log admin view"""
    name = "Webhook Log"
    name_plural = "Webhook Logs"
    icon = "fa-solid fa-webhook"
    
    required_permissions = [Permission.WEBHOOKS_READ]
    
    column_list = [
        WebhookLog.id,
        WebhookLog.event,
        WebhookLog.success,
        WebhookLog.processed_at
    ]
    column_searchable_list = [WebhookLog.event]
    column_filters = [WebhookLog.event, WebhookLog.success]
    column_sortable_list = [WebhookLog.processed_at]
    column_default_sort = [(WebhookLog.processed_at, True)]
    
    # Read-only view
    can_create = False
    can_edit = False
    can_delete = False
    
    # Show payload in details view
    column_details_list = [
        WebhookLog.id,
        WebhookLog.event,
        WebhookLog.success,
        WebhookLog.payload,
        WebhookLog.error,
        WebhookLog.processed_at
    ]


class AdminUserAdmin(SecureModelView, model=AdminUser):
    """Admin user management view"""
    name = "Admin User"
    name_plural = "Admin Users"
    icon = "fa-solid fa-user-shield"
    
    required_permissions = [Permission.ADMIN_USERS_READ]
    
    column_list = [
        AdminUser.id,
        AdminUser.email,
        AdminUser.full_name,
        AdminUser.is_active,
        AdminUser.is_superuser,
        AdminUser.last_login,
        AdminUser.created_at
    ]
    column_searchable_list = [AdminUser.email, AdminUser.full_name]
    column_filters = [AdminUser.is_active, AdminUser.is_superuser]
    column_sortable_list = [AdminUser.created_at, AdminUser.last_login]
    column_default_sort = [(AdminUser.created_at, True)]
    
    # Exclude password and sessions from forms
    form_excluded_columns = [AdminUser.password_hash, AdminUser.sessions, AdminUser.roles]
    
    # Custom form handling for password
    form_extra_fields = {
        'password': {
            'type': 'password',
            'required': False,
            'description': 'Leave empty to keep current password'
        }
    }
    
    # Handle password hashing on save
    async def on_model_change(self, data, model, is_created, request):
        """Hash password before saving"""
        if 'password' in data and data['password']:
            from src.admin.auth import get_password_hash
            model.password_hash = get_password_hash(data['password'])
        
        # Remove password from data to prevent SQLAlchemy error
        data.pop('password', None)
        
        return await super().on_model_change(data, model, is_created, request)


class AdminRoleAdmin(SecureModelView, model=AdminRole):
    """Admin role management view"""
    name = "Admin Role"
    name_plural = "Admin Roles"
    icon = "fa-solid fa-user-tag"
    
    required_permissions = [Permission.ADMIN_ROLES_READ]
    
    column_list = [
        AdminRole.id,
        AdminRole.name,
        AdminRole.description,
        AdminRole.is_system,
        AdminRole.created_at
    ]
    column_searchable_list = [AdminRole.name, AdminRole.description]
    column_filters = [AdminRole.is_system]
    column_sortable_list = [AdminRole.name, AdminRole.created_at]
    column_default_sort = [(AdminRole.created_at, True)]
    
    # Exclude users relationship from forms
    form_excluded_columns = [AdminRole.users]
    
    # System roles are read-only
    def can_edit(self, request) -> bool:
        """Only non-system roles can be edited"""
        if not super().can_edit(request):
            return False
        
        # Additional check would be needed per-row
        return True
    
    def can_delete(self, request) -> bool:
        """Only non-system roles can be deleted"""
        if not super().can_delete(request):
            return False
        
        # Additional check would be needed per-row
        return True


class RevenueRangeAdmin(SecureModelView, model=RevenueRange):
    """Revenue range admin view"""
    name = "Revenue Range"
    name_plural = "Revenue Ranges"
    icon = "fa-solid fa-chart-line"
    
    required_permissions = [Permission.PLANS_READ]
    
    column_list = [
        RevenueRange.id,
        RevenueRange.name,
        RevenueRange.min_revenue,
        RevenueRange.max_revenue,
        RevenueRange.sort_order,
        RevenueRange.created_at
    ]
    column_searchable_list = [RevenueRange.name]
    column_sortable_list = [RevenueRange.sort_order, RevenueRange.min_revenue]
    column_default_sort = [(RevenueRange.sort_order, False)]
    
    form_excluded_columns = [RevenueRange.plan_pricings]


class PlanPricingAdmin(SecureModelView, model=PlanPricing):
    """Plan pricing admin view"""
    name = "Plan Pricing"
    name_plural = "Plan Pricing"
    icon = "fa-solid fa-dollar-sign"
    
    required_permissions = [Permission.PLANS_READ]
    
    column_list = [
        PlanPricing.id,
        PlanPricing.plan,
        PlanPricing.revenue_range,
        PlanPricing.price,
        PlanPricing.created_at
    ]
    column_filters = [PlanPricing.plan, PlanPricing.revenue_range]
    column_sortable_list = [PlanPricing.price, PlanPricing.created_at]
    column_default_sort = [(PlanPricing.created_at, True)]


# Export all admin views
admin_views = [
    CustomerAdmin,
    PlanAdmin,
    AddonAdmin,
    SubscriptionAdmin,
    PaymentAdmin,
    WebhookLogAdmin,
    AdminUserAdmin,
    AdminRoleAdmin,
    RevenueRangeAdmin,
    PlanPricingAdmin
]