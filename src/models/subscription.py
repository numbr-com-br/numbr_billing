from sqlalchemy import Column, String, ForeignKey, Enum, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
from src.enums import SubscriptionStatus
import uuid


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    asaas_subscription_id = Column(String(255), nullable=True)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.PENDING)
    start_date = Column(DateTime, nullable=False, server_default=func.now())
    next_due_date = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    addons = relationship("SubscriptionAddon", back_populates="subscription")


class SubscriptionAddon(Base):
    __tablename__ = "subscription_addons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    addon_id = Column(String(36), ForeignKey("addons.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    subscription = relationship("Subscription", back_populates="addons")
    addon = relationship("Addon", back_populates="subscription_addons")
