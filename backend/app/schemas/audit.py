from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.utils.enums import AuditSource

class AuditLogOut(BaseModel):
    id: str
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    source: AuditSource
    ip_address: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogFilter(BaseModel):
    action: Optional[str] = None
    entity_type: Optional[str] = None
    source: Optional[AuditSource] = None
    actor_email: Optional[str] = None
