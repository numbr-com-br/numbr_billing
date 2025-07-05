from sqlalchemy import Column, String, Text, Numeric, Enum, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
from src.enums import AddonType
import uuid


class Addon(Base):
    __tablename__ = "addons"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(AddonType), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    subscription_addons = relationship("SubscriptionAddon", back_populates="addon")