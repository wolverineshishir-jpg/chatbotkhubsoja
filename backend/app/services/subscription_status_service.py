from app.models.enums import SubscriptionStatus


class SubscriptionStatusService:
    ACTIVE_STATUSES = {
        SubscriptionStatus.TRIALING,
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.PAST_DUE,
    }

    @classmethod
    def is_active_like(cls, status: SubscriptionStatus) -> bool:
        return status in cls.ACTIVE_STATUSES
