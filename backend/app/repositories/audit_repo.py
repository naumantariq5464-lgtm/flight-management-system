from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
import json
from app.models.audit import AuditLog
from app.utils.enums import AuditSource

class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_email: Optional[str] = None,
        actor_role: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        source: AuditSource = AuditSource.FASTAPI,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            actor_email=actor_email,
            actor_role=actor_role,
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str) if new_values else None,
            source=source,
            ip_address=ip_address,
            request_id=request_id
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        actor_email: Optional[str] = None,
        source: Optional[AuditSource] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        stmt = select(AuditLog)
        conditions = []
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if action:
            conditions.append(AuditLog.action == action)
        if actor_email:
            conditions.append(AuditLog.actor_email == actor_email)
        if source:
            conditions.append(AuditLog.source == source)
            
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
