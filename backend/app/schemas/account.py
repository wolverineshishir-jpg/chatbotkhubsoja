from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import MembershipRole
from app.schemas.common import ORMModel


class CreateAccountRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class JoinAccountRequest(BaseModel):
    onboarding_key: str = Field(..., min_length=12, max_length=64)


class CreateOnboardingKeyRequest(BaseModel):
    role: MembershipRole = MembershipRole.ADMIN
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_at: datetime | None = None
    invited_email: EmailStr | None = None


class AssignRoleRequest(BaseModel):
    role: MembershipRole


class CurrentAccountResponse(BaseModel):
    id: int
    name: str
    slug: str
    role: MembershipRole
    token_balance: int = 0
    monthly_token_credit: int = 0


class OnboardingKeyResponse(ORMModel):
    id: int
    key: str
    role: MembershipRole
    max_uses: int
    used_count: int
    expires_at: datetime | None
    revoked_at: datetime | None
    invited_email: EmailStr | None
