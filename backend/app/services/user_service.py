from app.models.membership import Membership
from app.models.user import User
from app.schemas.user import ManagedUserResponse, MembershipSummary, TeamMemberResponse, UserResponse


def build_user_response(user: User) -> UserResponse:
    memberships = [
        MembershipSummary(
            id=membership.id,
            account_id=membership.account_id,
            account_name=membership.account.name,
            account_slug=membership.account.slug,
            role=membership.role,
            status=membership.status,
        )
        for membership in user.memberships
    ]

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        user_role=user.user_role,
        is_superuser=user.is_superuser,
        permissions=list(user.permissions_json or []),
        memberships=memberships,
    )


def build_team_member_response(membership: Membership) -> TeamMemberResponse:
    return TeamMemberResponse(
        membership_id=membership.id,
        user_id=membership.user.id,
        email=membership.user.email,
        full_name=membership.user.full_name,
        role=membership.role,
        status=membership.user.status,
        joined_at=membership.created_at,
    )


def build_managed_user_response(user: User) -> ManagedUserResponse:
    membership = user.memberships[0] if user.memberships else None
    return ManagedUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        user_role=user.user_role,
        permissions=list(user.permissions_json or []),
        managed_by_user_id=user.managed_by_user_id,
        account_id=membership.account_id if membership else None,
        account_name=membership.account.name if membership else None,
        account_slug=membership.account.slug if membership else None,
        created_at=user.created_at,
    )
