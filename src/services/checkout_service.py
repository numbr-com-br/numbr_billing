from typing import List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Customer, Plan, Addon, Subscription
from src.schemas.checkout import CheckoutRequest, CheckoutResponse
from src.services.asaas import asaas_service
from src.services.customer_service import CustomerService
from src.services.subscription_service import SubscriptionService
from src.services.pricing_service import PricingService
from src.enums import SubscriptionStatus


class CheckoutService:
    """Service layer for checkout flow orchestration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.customer_service = CustomerService(db)
        self.subscription_service = SubscriptionService(db)
        self.pricing_service = PricingService(db)
    
    def process_checkout(
        self, 
        checkout_request: CheckoutRequest
    ) -> CheckoutResponse:
        """
        Process complete checkout flow:
        1. Validate plan and addons
        2. Create/update customer
        3. Calculate pricing
        4. Create subscription
        5. Generate payment link
        """
        # Validate plan
        plan = self._validate_plan(checkout_request.plan_id)
        
        # Validate addons
        addons = self._validate_addons(checkout_request.addon_ids)
        
        # Calculate total price
        total_price = self.pricing_service.calculate_checkout_price(
            plan=plan,
            addons=addons,
            annual_revenue=checkout_request.customer.annual_revenue
        )
        
        # Create or update customer
        customer, _ = self.customer_service.create_or_update_customer(
            checkout_request.customer
        )
        
        # Ensure customer has Asaas ID
        if not customer.asaas_customer_id:
            self._create_asaas_customer(customer)
        
        # Create subscription
        subscription = self._create_subscription(
            customer=customer,
            plan=plan,
            total_price=total_price,
            billing_type=checkout_request.billing_type
        )
        
        # Add subscription addons
        if addons:
            self.subscription_service.create_subscription_addons(
                subscription_id=subscription.id,
                addon_ids=[addon.id for addon in addons]
            )
        
        # Generate payment link
        payment_link = f"https://www.asaas.com/b/pay/{subscription.asaas_subscription_id}"
        
        return CheckoutResponse(
            subscription_id=subscription.id,
            customer_id=customer.id,
            payment_link=payment_link,
            total_price=total_price
        )
    
    def _validate_plan(self, plan_id: str) -> Plan:
        """Validate plan exists and is active."""
        plan = self.db.get(Plan, plan_id)
        if not plan or not plan.is_active:
            raise ValueError("Plan not found or inactive")
        return plan
    
    def _validate_addons(self, addon_ids: List[str]) -> List[Addon]:
        """Validate addons exist and are active."""
        if not addon_ids:
            return []
        
        result = self.db.execute(
            select(Addon).where(
                Addon.id.in_(addon_ids), 
                Addon.is_active.is_(True)
            )
        )
        addons = result.scalars().all()
        
        if len(addons) != len(addon_ids):
            raise ValueError("Some addons not found or inactive")
        
        return addons
    
    def _create_asaas_customer(self, customer: Customer) -> None:
        """Create customer in Asaas."""
        asaas_customer = asaas_service.create_customer({
            "name": customer.name,
            "email": customer.email,
            "cpfCnpj": customer.cpf_cnpj,
            "phone": customer.phone,
        })
        customer.asaas_customer_id = asaas_customer["id"]
        self.db.commit()
    
    def _create_subscription(
        self,
        customer: Customer,
        plan: Plan,
        total_price: Decimal,
        billing_type: str
    ) -> Subscription:
        """Create subscription locally and in Asaas."""
        # Create local subscription
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status=SubscriptionStatus.PENDING
        )
        self.db.add(subscription)
        self.db.commit()
        
        # Create Asaas subscription
        next_due_date = datetime.now() + timedelta(days=1)
        asaas_subscription = asaas_service.create_subscription({
            "customer": customer.asaas_customer_id,
            "billingType": billing_type,
            "value": float(total_price),
            "nextDueDate": next_due_date.strftime("%Y-%m-%d"),
            "cycle": plan.cycle.value,
            "description": f"{plan.name} subscription",
        })
        
        # Update local subscription with Asaas data
        subscription.asaas_subscription_id = asaas_subscription["id"]
        subscription.next_due_date = datetime.fromisoformat(
            asaas_subscription["nextDueDate"]
        )
        self.db.commit()
        
        return subscription