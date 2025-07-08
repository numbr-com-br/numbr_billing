from enum import Enum


class BillingCycle(str, Enum):
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMIANNUALLY = "SEMIANNUALLY"
    YEARLY = "YEARLY"


class AddonType(str, Enum):
    RECURRING = "RECURRING"
    ONE_TIME = "ONE_TIME"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    RECEIVED = "RECEIVED"
    OVERDUE = "OVERDUE"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class BillingType(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    BOLETO = "BOLETO"
    PIX = "PIX"
