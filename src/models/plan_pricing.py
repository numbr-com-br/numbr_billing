from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
import uuid


class PlanPricing(Base):
    __tablename__ = "plan_pricings"
    __table_args__ = (
        UniqueConstraint("plan_id", "revenue_range_id", name="uq_plan_revenue_range"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    revenue_range_id = Column(String(36), ForeignKey("revenue_ranges.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    plan = relationship("Plan", back_populates="plan_pricings")
    revenue_range = relationship("RevenueRange", back_populates="plan_pricings")
    
    def __repr__(self):
        return f"Pricing R$ {self.price:.2f}"
    
    def __str__(self):
        return self.__repr__()
