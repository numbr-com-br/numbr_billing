from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
import uuid


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    cpf_cnpj = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    asaas_customer_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    subscriptions = relationship("Subscription", back_populates="customer")