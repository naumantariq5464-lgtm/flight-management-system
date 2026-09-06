from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserOut
from app.models.user import User, Role
from app.repositories.user_repo import UserRepository
from app.repositories.audit_repo import AuditRepository
from app.auth.jwt import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.utils.enums import UserRole, AuditSource
from app.utils.exceptions import BadRequestException, UnauthorizedException
from app.utils.rate_limiter import login_rate_limiter, register_rate_limiter
from app.config.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register", 
    response_model=TokenResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limiter)]
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    # Check existing email
    existing = await user_repo.get_by_email(data.email)
    if existing:
        raise BadRequestException(f"User with email {data.email} already exists")

    # Public registration always creates a standard CUSTOMER
    customer_role_name = UserRole.CUSTOMER
    role = await user_repo.get_role_by_name(customer_role_name)
    if not role:
        role = Role(name=customer_role_name, description="Customer system role")
        db.add(role)
        await db.flush()

    user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role_id=role.id,
        is_active=True
    )
    user.role = role
    await user_repo.create_user(user)

    # Audit log
    await audit_repo.create_log(
        action="USER_REGISTERED",
        entity_type="User",
        entity_id=user.id,
        actor_email=user.email,
        source=AuditSource.FASTAPI
    )

    access_token = create_access_token(data={"sub": user.id, "role": user.role.name.value})
    user_out = UserOut.model_validate(user)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out
    )

@router.post(
    "/login", 
    response_model=TokenResponse,
    dependencies=[Depends(login_rate_limiter)]
)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(data.email)
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password credentials")
    if not user.is_active:
        raise BadRequestException("Account is disabled. Please contact support.")

    access_token = create_access_token(data={"sub": user.id, "role": user.role.name.value})
    user_out = UserOut.model_validate(user)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out
    )

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
