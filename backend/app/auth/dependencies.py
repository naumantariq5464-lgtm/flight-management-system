from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database.session import get_db
from app.auth.jwt import decode_access_token
from app.models.user import User
from app.utils.enums import UserRole
from app.utils.exceptions import UnauthorizedException, ForbiddenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        raise UnauthorizedException("Authentication token is missing")
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired authentication token")
    
    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException("User associated with token not found")
    if not user.is_active:
        raise ForbiddenException("User account is inactive")
    
    return user

async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except Exception:
        return None

def require_roles(*allowed_roles: UserRole):
    """Dependency factory checking that current user belongs to one of allowed roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise ForbiddenException(
                f"Access restricted. Required roles: {[r.value for r in allowed_roles]}, your role: {current_user.role.name.value}"
            )
        return current_user
    return role_checker

# Common role dependencies
get_admin_user = require_roles(UserRole.SUPER_ADMIN, UserRole.OPERATIONS_AGENT)
get_super_admin_user = require_roles(UserRole.SUPER_ADMIN)
