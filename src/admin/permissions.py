from enum import Enum
from typing import Dict, List, Set

class Permission(str, Enum):
    # Customers
    CUSTOMERS_READ = "customers:read"
    CUSTOMERS_WRITE = "customers:write"
    CUSTOMERS_DELETE = "customers:delete"
    
    # Plans
    PLANS_READ = "plans:read"
    PLANS_WRITE = "plans:write"
    PLANS_DELETE = "plans:delete"
    
    # Addons
    ADDONS_READ = "addons:read"
    ADDONS_WRITE = "addons:write"
    ADDONS_DELETE = "addons:delete"
    
    # Subscriptions
    SUBSCRIPTIONS_READ = "subscriptions:read"
    SUBSCRIPTIONS_WRITE = "subscriptions:write"
    SUBSCRIPTIONS_CANCEL = "subscriptions:cancel"
    
    # Payments
    PAYMENTS_READ = "payments:read"
    PAYMENTS_REFUND = "payments:refund"
    
    # Webhooks
    WEBHOOKS_READ = "webhooks:read"
    
    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"
    
    # Admin Management
    ADMIN_USERS_READ = "admin:users:read"
    ADMIN_USERS_WRITE = "admin:users:write"
    ADMIN_ROLES_READ = "admin:roles:read"
    ADMIN_ROLES_WRITE = "admin:roles:write"


# Permission descriptions for UI
PERMISSION_DESCRIPTIONS: Dict[Permission, str] = {
    Permission.CUSTOMERS_READ: "View customers",
    Permission.CUSTOMERS_WRITE: "Create and edit customers",
    Permission.CUSTOMERS_DELETE: "Delete customers",
    
    Permission.PLANS_READ: "View plans",
    Permission.PLANS_WRITE: "Create and edit plans",
    Permission.PLANS_DELETE: "Delete plans",
    
    Permission.ADDONS_READ: "View addons",
    Permission.ADDONS_WRITE: "Create and edit addons",
    Permission.ADDONS_DELETE: "Delete addons",
    
    Permission.SUBSCRIPTIONS_READ: "View subscriptions",
    Permission.SUBSCRIPTIONS_WRITE: "Create and edit subscriptions",
    Permission.SUBSCRIPTIONS_CANCEL: "Cancel subscriptions",
    
    Permission.PAYMENTS_READ: "View payments",
    Permission.PAYMENTS_REFUND: "Process refunds",
    
    Permission.WEBHOOKS_READ: "View webhook logs",
    
    Permission.REPORTS_VIEW: "View reports and analytics",
    Permission.REPORTS_EXPORT: "Export data",
    
    Permission.ADMIN_USERS_READ: "View admin users",
    Permission.ADMIN_USERS_WRITE: "Manage admin users",
    Permission.ADMIN_ROLES_READ: "View roles",
    Permission.ADMIN_ROLES_WRITE: "Manage roles and permissions",
}


# Default system roles
class SystemRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPPORT = "support"
    FINANCE = "finance"
    VIEWER = "viewer"


# Role configurations
SYSTEM_ROLES: Dict[SystemRole, Dict] = {
    SystemRole.SUPER_ADMIN: {
        "name": "Super Admin",
        "description": "Full system access",
        "permissions": list(Permission)  # All permissions
    },
    SystemRole.ADMIN: {
        "name": "Administrator",
        "description": "Full access except admin management",
        "permissions": [
            p for p in Permission 
            if not p.value.startswith("admin:")
        ]
    },
    SystemRole.SUPPORT: {
        "name": "Support",
        "description": "Customer and subscription management",
        "permissions": [
            Permission.CUSTOMERS_READ,
            Permission.CUSTOMERS_WRITE,
            Permission.PLANS_READ,
            Permission.ADDONS_READ,
            Permission.SUBSCRIPTIONS_READ,
            Permission.SUBSCRIPTIONS_WRITE,
            Permission.SUBSCRIPTIONS_CANCEL,
            Permission.PAYMENTS_READ,
            Permission.WEBHOOKS_READ,
        ]
    },
    SystemRole.FINANCE: {
        "name": "Finance",
        "description": "Financial operations and reporting",
        "permissions": [
            Permission.CUSTOMERS_READ,
            Permission.PLANS_READ,
            Permission.SUBSCRIPTIONS_READ,
            Permission.PAYMENTS_READ,
            Permission.PAYMENTS_REFUND,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_EXPORT,
        ]
    },
    SystemRole.VIEWER: {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            Permission.CUSTOMERS_READ,
            Permission.PLANS_READ,
            Permission.ADDONS_READ,
            Permission.SUBSCRIPTIONS_READ,
            Permission.PAYMENTS_READ,
            Permission.WEBHOOKS_READ,
            Permission.REPORTS_VIEW,
        ]
    }
}


def get_role_permissions(role_name: str) -> List[str]:
    """Get permissions for a system role"""
    for system_role in SystemRole:
        if system_role.value == role_name:
            role_config = SYSTEM_ROLES[system_role]
            return [p.value for p in role_config["permissions"]]
    return []


def get_permission_groups() -> Dict[str, List[Permission]]:
    """Group permissions by resource for UI display"""
    groups = {
        "Customers": [],
        "Plans": [],
        "Addons": [],
        "Subscriptions": [],
        "Payments": [],
        "Reports": [],
        "Administration": [],
        "Other": []
    }
    
    for perm in Permission:
        if perm.value.startswith("customers:"):
            groups["Customers"].append(perm)
        elif perm.value.startswith("plans:"):
            groups["Plans"].append(perm)
        elif perm.value.startswith("addons:"):
            groups["Addons"].append(perm)
        elif perm.value.startswith("subscriptions:"):
            groups["Subscriptions"].append(perm)
        elif perm.value.startswith("payments:"):
            groups["Payments"].append(perm)
        elif perm.value.startswith("reports:"):
            groups["Reports"].append(perm)
        elif perm.value.startswith("admin:"):
            groups["Administration"].append(perm)
        else:
            groups["Other"].append(perm)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}