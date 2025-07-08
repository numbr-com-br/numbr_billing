from starlette.requests import Request
from sqladmin import BaseView, expose
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.models import Customer, Plan, Addon, RevenueRange, PlanPricing, Subscription, SubscriptionAddon
from src.enums import SubscriptionStatus, BillingType
from src.services.asaas_service import AsaasService
from src.admin.permissions import Permission
from src.config import settings


class CheckoutGeneratorView(BaseView):
    """Custom admin view for generating Asaas checkout links"""
    
    name = "Generate Checkout Link"
    icon = "fa-solid fa-link"
    
    def is_accessible(self, request: Request) -> bool:
        """Check if user has permission to access this view"""
        if not request.session.get("user_id"):
            return False
        
        # Superusers have all access
        if request.session.get("is_superuser"):
            return True
        
        # Check permissions
        user_permissions = request.session.get("permissions", [])
        return Permission.CUSTOMERS_WRITE.value in user_permissions
    
    def is_visible(self, request: Request) -> bool:
        """Check if view should be visible in menu"""
        return self.is_accessible(request)
    
    @expose("/generate", methods=["GET", "POST"])
    async def generate_checkout(self, request: Request):
        """Generate checkout link page"""
        if request.method == "GET":
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
            
            return await self.templates.render(
                request,
                "admin/checkout_generator.html",
                context={
                    "customer_choices": customer_choices,
                    "plan_choices": plan_choices,
                    "revenue_range_choices": revenue_range_choices,
                    "addon_choices": addon_choices,
                    "billing_type_choices": billing_type_choices,
                }
            )
        
        form_data = await request.form()
        
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
            return await self.templates.render(
                request,
                "admin/checkout_generator.html",
                context={
                    "errors": errors,
                    "form_data": form_data,
                }
            )
        
        asaas_service = AsaasService(api_key=settings.asaas_api_key)
        
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
                errors.append(f"No pricing found for {plan.name} in {revenue_range.name}")
                return await self.templates.render(
                    request,
                    "admin/checkout_generator.html",
                    context={"errors": errors, "form_data": form_data}
                )
            
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
            
            # Show success with payment link
            return await self.templates.render(
                request,
                "admin/checkout_success.html",
                context={
                    "customer": customer,
                    "plan": plan,
                    "revenue_range": revenue_range,
                    "addons": addons,
                    "total_price": total_price,
                    "payment_link": payment_link,
                    "subscription_id": subscription.id,
                }
            )