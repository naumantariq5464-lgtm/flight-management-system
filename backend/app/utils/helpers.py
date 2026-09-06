import random
import string
from datetime import datetime, timezone

def generate_pnr(length: int = 6) -> str:
    """Generate a 6-character alphanumeric PNR / Booking Reference (uppercase letters and digits, excluding ambiguous chars)."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))

def generate_ticket_number() -> str:
    """Generate a 13-digit e-ticket number."""
    prefix = "176"  # Airline accounting code
    rest = "".join(random.choices(string.digits, k=10))
    return f"{prefix}-{rest}"

def generate_credit_code() -> str:
    """Generate a 10-character travel credit voucher code."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "TC-" + "".join(random.choices(chars, k=8))

def utc_now() -> datetime:
    """Get current UTC timezone-aware datetime."""
    return datetime.now(timezone.utc)
