from flask import render_template, request, redirect, url_for, flash
from flask_admin import BaseView, expose
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.models import Customer, Plan, Addon, RevenueRange, PlanPricing, Subscription, SubscriptionAddon
from src.enums import SubscriptionStatus, BillingType
from src.services.asaas import AsaasService
from src.admin.permissions import Permission
from src.config import settings


class CheckoutGeneratorView(BaseView):
    """Custom admin view for generating Asaas checkout links"""
    
    def is_accessible(self):
        """Check if current user has access to this view"""
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            
            if not user_id:
                return False
            
            db = SessionLocal()
            try:
                from src.models.admin_user import AdminUser
                user = db.query(AdminUser).filter_by(id=user_id).first()
                if not user or not user.is_active:
                    return False
                
                return user.has_permission(Permission.CUSTOMERS_WRITE)
            finally:
                db.close()
        except:
            return False
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to login page when access is denied"""
        return redirect(url_for('admin_auth.login', next=request.url))
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Generate checkout link page"""
        if request.method == 'GET':
            with SessionLocal() as db:
                result = db.execute(
                    select(Customer).order_by(Customer.name)
                )
                customers = result.scalars().all()
                
                result = db.execute(
                    select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.name)
                )
                plans = result.scalars().all()
                
                result = db.execute(
                    select(RevenueRange).order_by(RevenueRange.sort_order)
                )
                revenue_ranges = result.scalars().all()
                
                result = db.execute(
                    select(Addon).where(Addon.is_active.is_(True)).order_by(Addon.name)
                )
                addons = result.scalars().all()
            
            customer_choices = [("", "Select existing customer...")] + [
                (str(c.id), f"{c.name} ({c.email})") for c in customers
            ]
            plan_choices = [(str(p.id), f"{p.name} ({p.cycle.value})") for p in plans]
            revenue_range_choices = [(str(r.id), str(r)) for r in revenue_ranges]
            addon_choices = [(str(a.id), f"{a.name} - R$ {a.price:.2f}") for a in addons]
            billing_type_choices = [
                (BillingType.CREDIT_CARD.value, "Credit Card"),
                (BillingType.BOLETO.value, "Boleto"),
                (BillingType.PIX.value, "PIX"),
            ]
            
            return self.render(
                'admin/checkout_generator.html',
                customer_choices=customer_choices,
                plan_choices=plan_choices,
                revenue_range_choices=revenue_range_choices,
                addon_choices=addon_choices,
                billing_type_choices=billing_type_choices,
            )
        
        # POST - Process form
        form_data = request.form
        
        errors = []
        if not form_data.get("plan_id"):
            errors.append("Plan is required")
        if not form_data.get("revenue_range_id"):
            errors.append("Revenue range is required")
        if not form_data.get("billing_type"):
            errors.append("Billing type is required")
        
        customer_id = form_data.get("customer_id")
        if not customer_id:
            if not form_data.get("new_customer_name"):
                errors.append("Customer name is required for new customer")
            if not form_data.get("new_customer_email"):
                errors.append("Customer email is required for new customer")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('.index'))
        
        asaas_service = AsaasService()
        
        with SessionLocal() as db:
            if customer_id:
                customer = db.get(Customer, customer_id)
            else:
                result = db.execute(
                    select(Customer).where(Customer.email == form_data.get("new_customer_email"))
                )
                customer = result.scalar_one_or_none()
                
                if not customer:
                    customer = Customer(
                        name=form_data.get("new_customer_name"),
                        email=form_data.get("new_customer_email"),
                        cpf_cnpj=form_data.get("new_customer_cpf_cnpj"),
                        phone=form_data.get("new_customer_phone"),
                    )
                    db.add(customer)
            
            revenue_range = db.get(RevenueRange, form_data.get("revenue_range_id"))
            customer.annual_revenue = revenue_range.min_revenue
            
            plan = db.get(Plan, form_data.get("plan_id"))
            
            result = db.execute(
                select(PlanPricing).where(
                    PlanPricing.plan_id == plan.id,
                    PlanPricing.revenue_range_id == revenue_range.id
                )
            )
            plan_pricing = result.scalar_one_or_none()
            
            if not plan_pricing:
                flash(f"No pricing found for {plan.name} in {revenue_range.name}", 'error')
                return redirect(url_for('.index'))
            
            total_price = Decimal(str(plan_pricing.price))
            
            addon_ids = form_data.getlist("addon_ids")
            addons = []
            if addon_ids:
                result = db.execute(
                    select(Addon).where(Addon.id.in_(addon_ids))
                )
                addons = result.scalars().all()
                for addon in addons:
                    total_price += Decimal(str(addon.price))
            
            db.commit()
            
            if not customer.asaas_customer_id:
                asaas_customer = asaas_service.create_customer({
                    "name": customer.name,
                    "email": customer.email,
                    "cpfCnpj": customer.cpf_cnpj,
                    "phone": customer.phone,
                })
                customer.asaas_customer_id = asaas_customer["id"]
                db.commit()
            
            subscription = Subscription(
                customer_id=customer.id,
                plan_id=plan.id,
                status=SubscriptionStatus.PENDING
            )
            db.add(subscription)
            db.commit()
            
            for addon in addons:
                subscription_addon = SubscriptionAddon(
                    subscription_id=subscription.id,
                    addon_id=addon.id,
                    quantity=1
                )
                db.add(subscription_addon)
            
            db.commit()
            
            next_due_date = datetime.now() + timedelta(days=1)
            asaas_subscription = asaas_service.create_subscription({
                "customer": customer.asaas_customer_id,
                "billingType": form_data.get("billing_type"),
                "value": float(total_price),
                "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
                "cycle": plan.cycle.value,
                "description": f"{plan.name} subscription",
            })
            
            subscription.asaas_subscription_id = asaas_subscription["id"]
            subscription.next_due_date = datetime.fromisoformat(asaas_subscription["nextDueDate"])
            db.commit()
            
            payment_link = f"https://www.asaas.com/b/pay/{asaas_subscription['id']}"
            
            return self.render(
                'admin/checkout_success.html',
                customer=customer,
                plan=plan,
                revenue_range=revenue_range,
                addons=addons,
                total_price=total_price,
                payment_link=payment_link,
                subscription_id=subscription.id,
            )