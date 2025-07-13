from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models import Customer, Subscription
from src.schemas.customer import CustomerCreate, CustomerUpdate
from src.services.asaas import asaas_service
from src.enums import SubscriptionStatus


class CustomerService:
    """Service layer for customer-related business logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update_customer(
        self, 
        customer_data: CustomerCreate
    ) -> Tuple[Customer, bool]:
        """
        Create a new customer or update existing one based on email.
        Returns tuple of (customer, is_new).
        """
        result = self.db.execute(
            select(Customer).where(Customer.email == customer_data.email)
        )
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            # Update existing customer
            for field, value in customer_data.model_dump(exclude_unset=True).items():
                setattr(existing_customer, field, value)
            customer = existing_customer
            is_new = False
        else:
            # Create new customer
            customer = Customer(**customer_data.model_dump())
            self.db.add(customer)
            is_new = True
        
        self.db.commit()
        
        # Sync with Asaas if needed
        if not customer.asaas_customer_id:
            self._sync_customer_with_asaas(customer)
        
        return customer, is_new
    
    def update_customer(
        self, 
        customer_id: str, 
        update_data: CustomerUpdate
    ) -> Optional[Customer]:
        """Update customer by ID."""
        customer = self.db.get(Customer, customer_id)
        if not customer:
            return None
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)
        
        self.db.commit()
        return customer
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email."""
        result = self.db.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()
    
    def get_customer_subscription_counts(
        self, 
        customer_id: str
    ) -> Tuple[int, int]:
        """
        Get active and total subscription counts for a customer.
        Returns tuple of (active_count, total_count).
        """
        active_count = self.db.execute(
            select(func.count(Subscription.id))
            .where(
                Subscription.customer_id == customer_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).scalar()
        
        total_count = self.db.execute(
            select(func.count(Subscription.id))
            .where(Subscription.customer_id == customer_id)
        ).scalar()
        
        return active_count, total_count
    
    def _sync_customer_with_asaas(self, customer: Customer) -> None:
        """Create customer in Asaas and update local record."""
        try:
            asaas_customer = asaas_service.create_customer({
                "name": customer.name,
                "email": customer.email,
                "cpfCnpj": customer.cpf_cnpj,
                "phone": customer.phone,
            })
            customer.asaas_customer_id = asaas_customer["id"]
            self.db.commit()
        except Exception as e:
            print(f"Failed to create Asaas customer: {e}")
            # Business decision: Continue without Asaas sync
            # This will be retried on next checkout attempt