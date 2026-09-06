from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.audit import AuditLogOut
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.auth.dependencies import get_admin_user
from app.utils.enums import AuditSource

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Logs"])

@router.get("", response_model=List[AuditLogOut])
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    actor_email: Optional[str] = None,
    source: Optional[AuditSource] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AuditRepository(db)
    logs = await repo.list_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_email=actor_email,
        source=source,
        skip=skip,
        limit=limit
    )
    return [AuditLogOut.model_validate(l) for l in logs]
