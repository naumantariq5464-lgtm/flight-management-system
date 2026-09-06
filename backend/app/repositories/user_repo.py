from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.user import User, Role, Permission
from app.utils.enums import UserRole

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).options(selectinload(User.role)).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, role_name: UserRole) -> Optional[Role]:
        stmt = select(Role).where(Role.name == role_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def list_users(self, role_name: Optional[UserRole] = None, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).options(selectinload(User.role))
        if role_name:
            stmt = stmt.join(User.role).where(Role.name == role_name)
        stmt = stmt.order_by(desc(User.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
