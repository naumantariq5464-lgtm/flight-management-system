from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.utils.enums import UserRole

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"

class PermissionOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleOut(BaseModel):
    id: str
    name: UserRole
    description: Optional[str] = None
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_active: bool
    loyalty_tier: str
    role: RoleOut
    created_at: datetime

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()
