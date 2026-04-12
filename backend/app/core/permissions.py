from collections.abc import Iterable

from app.models.enums import MembershipRole, UserRole

ROLE_PERMISSIONS: dict[MembershipRole, set[str]] = {
    MembershipRole.OWNER: {
        "account:manage",
        "team:read",
        "team:manage",
        "key:manage",
        "connection:read",
        "connection:manage",
        "inbox:read",
        "inbox:manage",
        "comments:read",
        "comments:manage",
        "posts:read",
        "posts:manage",
        "ai:read",
        "ai:manage",
        "automation:read",
        "automation:manage",
        "reports:read",
    },
    MembershipRole.ADMIN: {
        "team:read",
        "team:manage",
        "key:manage",
        "connection:read",
        "connection:manage",
        "inbox:read",
        "inbox:manage",
        "comments:read",
        "comments:manage",
        "posts:read",
        "posts:manage",
        "ai:read",
        "ai:manage",
        "automation:read",
        "automation:manage",
        "reports:read",
    },
}


def has_permissions(role: MembershipRole, required_permissions: Iterable[str]) -> bool:
    available = ROLE_PERMISSIONS.get(role, set())
    return set(required_permissions).issubset(available)


def has_user_permissions(user_role: UserRole, role: MembershipRole, custom_permissions: Iterable[str], required_permissions: Iterable[str]) -> bool:
    if user_role in {UserRole.OWNER, UserRole.SUPER_ADMIN}:
        return True

    custom_permissions_set = set(custom_permissions)
    if custom_permissions_set:
        return set(required_permissions).issubset(custom_permissions_set)

    return has_permissions(role, required_permissions)
