from sqlalchemy import Column, String, Text, Enum, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
from src.enums import BillingCycle
import uuid


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cycle = Column(Enum(BillingCycle), nullable=False)
    features = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")
    plan_pricings = relationship("PlanPricing", back_populates="plan", cascade="all, delete-orphan")
