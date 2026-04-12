from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import ActionUsageType, ConnectionStatus
from app.models.platform_connection import PlatformConnection
from app.models.refresh_token import RefreshToken
from app.services.billing_service import BillingService
from app.services.observability_service import ObservabilityService


class TokenMaintenanceService:
    def __init__(self, db: Session):
        self.db = db

    def apply_monthly_credits(self) -> int:
        now = self._utcnow()
        accounts = self.db.scalars(
            select(Account).where(
                Account.is_active.is_(True),
                Account.monthly_token_credit > 0,
                (
                    (Account.token_credit_next_reset_at.is_(None))
                    | (Account.token_credit_next_reset_at <= now)
                ),
            )
        ).all()
        for account in accounts:
            BillingService(self.db).apply_monthly_credit(account=account)
            ObservabilityService(self.db).record_action_usage(
                account_id=account.id,
                action_type=ActionUsageType.TOKEN_CREDIT,
                quantity=1,
                tokens_consumed=0,
                estimated_cost=Decimal("0"),
                metadata_json={"monthly_token_credit": account.monthly_token_credit},
            )
        self.db.commit()
        return len(accounts)

    def expire_tokens(self) -> dict[str, int]:
        now = self._utcnow()
        revoked = 0
        refreshed_connections = 0
        expired_wallet_tokens = BillingService(self.db).expire_monthly_tokens()

        tokens = self.db.scalars(
            select(RefreshToken).where(
                RefreshToken.expires_at <= now,
                RefreshToken.revoked_at.is_(None),
            )
        ).all()
        for token in tokens:
            token.revoked_at = now
            revoked += 1

        connections = self.db.scalars(select(PlatformConnection)).all()
        for connection in connections:
            expires_at = connection.metadata_json.get("access_token_expires_at")
            if not expires_at:
                continue
            expiry = self._parse_datetime(expires_at)
            if expiry and expiry <= now and connection.status != ConnectionStatus.ACTION_REQUIRED:
                connection.status = ConnectionStatus.ACTION_REQUIRED
                connection.last_error = "Access token expired and needs refresh."
                refreshed_connections += 1
                ObservabilityService(self.db).record_action_usage(
                    account_id=connection.account_id,
                    platform_connection_id=connection.id,
                    platform_type=connection.platform_type,
                    action_type=ActionUsageType.TOKEN_EXPIRATION,
                    quantity=1,
                    tokens_consumed=0,
                    estimated_cost=Decimal("0"),
                    metadata_json={"connection_status": connection.status.value},
                )

        self.db.commit()
        return {
            "revoked_refresh_tokens": revoked,
            "connections_marked_action_required": refreshed_connections,
            "expired_wallet_tokens": expired_wallet_tokens,
        }

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
