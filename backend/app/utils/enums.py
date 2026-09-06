import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OPERATIONS_AGENT = "OPERATIONS_AGENT"
    CUSTOMER = "CUSTOMER"

class FlightStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    BOARDING = "BOARDING"
    DEPARTED = "DEPARTED"
    ARRIVED = "ARRIVED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"

class SeatClass(str, enum.Enum):
    FIRST = "FIRST"
    BUSINESS = "BUSINESS"
    ECONOMY = "ECONOMY"

class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"
    RELEASED = "RELEASED"

class FareType(str, enum.Enum):
    BASIC_ECONOMY = "BASIC_ECONOMY"
    FLEXIBLE = "FLEXIBLE"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    REBOOKED = "REBOOKED"

class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"

class RefundType(str, enum.Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    TAX_ONLY = "TAX_ONLY"
    COMPENSATION = "COMPENSATION"

class CreditStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class WaitlistStatus(str, enum.Enum):
    WAITING = "WAITING"
    PROMOTED = "PROMOTED"
    CLAIMED = "CLAIMED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class FraudStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"

class AuditSource(str, enum.Enum):
    FASTAPI = "FASTAPI"
    N8N = "N8N"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"

class OverbookingPolicy(str, enum.Enum):
    HARD_NEVER_OVERSELL = "HARD_NEVER_OVERSELL"
    CONTROLLED_BUFFER = "CONTROLLED_BUFFER"

class GroupBookingPolicy(str, enum.Enum):
    FULL_FAILURE = "FULL_FAILURE"
    PARTIAL_HOLD = "PARTIAL_HOLD"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"

class RagApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EDITED = "EDITED"

class NotificationType(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"
