from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone
from app.models.idempotency import IdempotencyKey

class IdempotencyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_key(self, key: str, for_update: bool = False) -> Optional[IdempotencyKey]:
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_key(self, key: str, request_path: str, payload_hash: Optional[str] = None) -> IdempotencyKey:
        record = IdempotencyKey(
            key=key,
            request_path=request_path,
            request_payload_hash=payload_hash,
            locked_at=datetime.now(timezone.utc)
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def complete_key(self, record: IdempotencyKey, status_code: int, response_body: str) -> IdempotencyKey:
        record.response_code = status_code
        record.response_body = response_body
        record.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return record
