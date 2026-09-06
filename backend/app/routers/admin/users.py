from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.auth import UserOut, UserRegister
from app.models.user import User, Role
from app.repositories.user_repo import UserRepository
from app.repositories.audit_repo import AuditRepository
from app.auth.jwt import get_password_hash
from app.auth.dependencies import get_super_admin_user
from app.utils.enums import UserRole, AuditSource
from app.utils.exceptions import BadRequestException

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

@router.get("", response_model=List[UserOut])
async def list_users(
    role: Optional[UserRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    users = await repo.list_users(role_name=role, skip=skip, limit=limit)
    return [UserOut.model_validate(u) for u in users]

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    data: UserRegister,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    existing = await user_repo.get_by_email(data.email)
    if existing:
        raise BadRequestException(f"User {data.email} already exists")

    role = await user_repo.get_role_by_name(data.role)
    if not role:
        role = Role(name=data.role, description=f"{data.role.value} role")
        db.add(role)
        await db.flush()

    new_user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role_id=role.id,
        is_active=True
    )
    await user_repo.create_user(new_user)

    await audit_repo.create_log(
        action="STAFF_USER_CREATED",
        entity_type="User",
        entity_id=new_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role.name.value,
        new_values={"email": new_user.email, "role": data.role.value},
        source=AuditSource.ADMIN
    )

    return UserOut.model_validate(new_user)
