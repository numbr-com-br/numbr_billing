from sqlalchemy import Column, String, JSON, Boolean, DateTime, Text
from sqlalchemy.sql import func
from src.database import Base
import uuid


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=False, server_default=func.now())
    
    def __repr__(self):
        status = "Success" if self.success else "Error"
        return f"Webhook {self.event} - {status}"
    
    def __str__(self):
        return self.__repr__()
