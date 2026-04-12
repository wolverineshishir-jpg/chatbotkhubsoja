from datetime import datetime

from pydantic import EmailStr, Field

from app.models.enums import MembershipRole, MembershipStatus, UserRole, UserStatus
from app.schemas.common import APIModel, ORMModel


class MembershipSummary(ORMModel):
    id: int
    account_id: int
    account_name: str
    account_slug: str
    role: MembershipRole
    status: MembershipStatus


class UserResponse(ORMModel):
    id: int
    email: str
    full_name: str | None
    status: UserStatus
    user_role: UserRole
    is_superuser: bool
    permissions: list[str]
    memberships: list[MembershipSummary]


class TeamMemberResponse(ORMModel):
    membership_id: int
    user_id: int
    email: str
    full_name: str | None
    role: MembershipRole
    status: UserStatus
    joined_at: datetime


class ManagedUserResponse(ORMModel):
    id: int
    email: str
    full_name: str | None
    status: UserStatus
    user_role: UserRole
    permissions: list[str]
    managed_by_user_id: int | None
    account_id: int | None = None
    account_name: str | None = None
    account_slug: str | None = None
    created_at: datetime


class CreateSuperAdminRequest(APIModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    status: UserStatus = UserStatus.ACTIVE
    account_name: str = Field(..., min_length=2, max_length=255)
    account_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    permissions: list[str] = Field(default_factory=list)


class UpdateSuperAdminRequest(APIModel):
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    status: UserStatus | None = None
    permissions: list[str] | None = None


class CreateAdminRequest(APIModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    status: UserStatus = UserStatus.ACTIVE
    permissions: list[str] = Field(default_factory=list)


class UpdateAdminRequest(APIModel):
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    status: UserStatus | None = None
    permissions: list[str] | None = None
