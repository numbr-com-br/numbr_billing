import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.database import SessionLocal
from src.models.admin_user import AdminUser, AdminRole
from src.admin.permissions import Permission, SYSTEM_ROLES
from src.admin.auth import get_password_hash


def create_system_roles():
    """Create system roles if they don't exist"""
    with SessionLocal() as db:
        # Check if roles already exist
        existing_roles = db.execute(select(AdminRole.name))
        existing_role_names = {role[0] for role in existing_roles}
        
        roles_created = []
        for role_name, role_config in SYSTEM_ROLES.items():
            if role_name not in existing_role_names:
                role = AdminRole(
                    name=role_name,
                    description=role_config["description"],
                    permissions=role_config["permissions"],
                    is_system=True
                )
                db.add(role)
                roles_created.append(role_name)
        
        if roles_created:
            db.commit()
            print(f"✅ Created system roles: {', '.join(roles_created)}")
        else:
            print("ℹ️  System roles already exist")
        
        return roles_created


def create_superuser(email: str, password: str):
    """Create a superuser account"""
    with SessionLocal() as db:
        # Check if user already exists
        result = db.execute(select(AdminUser).where(AdminUser.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"ℹ️  User {email} already exists")
            return
        
        # Create superuser
        superuser = AdminUser(
            email=email,
            password_hash=get_password_hash(password),
            full_name="System Administrator",
            is_active=True,
            is_superuser=True
        )
        
        # Get super admin role
        role_result = db.execute(
            select(AdminRole).where(AdminRole.name == "Super Admin")
        )
        super_admin_role = role_result.scalar_one_or_none()
        
        if super_admin_role:
            superuser.roles.append(super_admin_role)
        
        db.add(superuser)
        db.commit()
        
        print(f"✅ Created superuser: {email}")


def main():
    """Main function to seed admin data"""
    print("🌱 Seeding admin data...")
    
    # Create system roles
    create_system_roles()
    
    # Create default superuser
    # In production, these should come from environment variables
    default_email = "admin@numbr.com.br"
    default_password = "AdminNumbr2025!"
    
    print(f"\n📧 Creating superuser with email: {default_email}")
    create_superuser(default_email, default_password)
    
    print("\n✨ Admin seeding completed!")
    print("\n🔐 Login credentials:")
    print(f"   Email: {default_email}")
    print(f"   Password: {default_password}")
    print("\n⚠️  Please change the password after first login!")


if __name__ == "__main__":
    main()