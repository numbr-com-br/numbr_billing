from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
from src.enums import PaymentStatus
import uuid


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    asaas_payment_id = Column(String(255), nullable=True)
    payment_link = Column(String(255), nullable=True)
    invoice_number = Column(String(255), nullable=True)
    transaction_receipt = Column(String(255), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    billing_type = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    external_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self):
        return f"Payment R$ {self.amount:.2f} - {self.status.value}"

    def __str__(self):
        return self.__repr__()
