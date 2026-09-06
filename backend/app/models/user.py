from sqlalchemy import String, Boolean, ForeignKey, Table, Column, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin
from app.utils.enums import UserRole
import uuid

# Association table for Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship("Permission", secondary=role_permissions, lazy="selectin")
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    loyalty_tier: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)  # STANDARD, SILVER, GOLD, PLATINUM
    
    role_id: Mapped[str] = mapped_column(String, ForeignKey("roles.id"), nullable=False)
    
    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")
    travel_credits: Mapped[list["TravelCredit"]] = relationship("TravelCredit", back_populates="user")
    price_alerts: Mapped[list["PriceAlert"]] = relationship("PriceAlert", back_populates="user")
