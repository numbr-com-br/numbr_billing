from sqlalchemy import Column, String, Numeric, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
import uuid


class RevenueRange(Base):
    __tablename__ = "revenue_ranges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    min_revenue = Column(Numeric(15, 2), nullable=False)
    max_revenue = Column(Numeric(15, 2), nullable=True)  # NULL means no upper limit
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    plan_pricings = relationship("PlanPricing", back_populates="revenue_range")
    
    def __repr__(self):
        if self.max_revenue:
            return f"{self.name} (R$ {self.min_revenue:,.2f} - R$ {self.max_revenue:,.2f})"
        else:
            return f"{self.name} (R$ {self.min_revenue:,.2f}+)"
    
    def __str__(self):
        return self.__repr__()
