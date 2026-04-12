from datetime import UTC, datetime
import os
import sys
from pathlib import Path

from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "seed-secret-key-with-at-least-32-characters")

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.account_subscription import AccountSubscription
from app.models.billing_plan import BillingPlan
from app.models.enums import BillingInterval, MembershipRole, MembershipStatus, SubscriptionStatus
from app.models.membership import Membership
from app.services.token_wallet_service import TokenWalletService
from app.services.user_management_service import UserManagementService
from scripts.seed_system_data import main as seed_system_data_main


def main() -> None:
    try:
        seed_system_data_main()
        settings = get_settings()
        db = SessionLocal()
        try:
            owner = UserManagementService(db).ensure_owner_user()

            starter_plan = db.scalar(select(BillingPlan).where(BillingPlan.code == "starter_monthly"))
            if starter_plan is None:
                starter_plan = BillingPlan(
                    code="starter_monthly",
                    name="Starter Monthly",
                    description="Starter plan for teams getting started with automation.",
                    billing_interval=BillingInterval.MONTHLY,
                    price_usd=29,
                    monthly_token_credit=15000,
                    is_active=True,
                    metadata_json={"seeded_by": "seed_local_data"},
                )
                db.add(starter_plan)
                db.flush()

            account = db.scalar(select(Account).where(Account.slug == "local-workspace"))
            if account is None:
                account = Account(
                    name="Local Workspace",
                    slug="local-workspace",
                    token_balance=10000,
                    monthly_token_credit=5000,
                    token_credit_last_applied_at=datetime.now(UTC),
                )
                db.add(account)
                db.flush()

            membership = db.scalar(
                select(Membership).where(Membership.account_id == account.id, Membership.user_id == owner.id)
            )
            if membership is None:
                db.add(
                    Membership(
                        account_id=account.id,
                        user_id=owner.id,
                        role=MembershipRole.OWNER,
                        status=MembershipStatus.ACTIVE,
                    )
                )

            subscription = db.scalar(
                select(AccountSubscription).where(
                    AccountSubscription.account_id == account.id,
                    AccountSubscription.billing_plan_id == starter_plan.id,
                    AccountSubscription.status == SubscriptionStatus.ACTIVE,
                )
            )
            if subscription is None:
                db.add(
                    AccountSubscription(
                        account_id=account.id,
                        billing_plan_id=starter_plan.id,
                        status=SubscriptionStatus.ACTIVE,
                        starts_at=datetime.now(UTC),
                        renews_at=datetime.now(UTC),
                        metadata_json={"seeded_by": "seed_local_data"},
                    )
                )

            TokenWalletService(db).ensure_wallet(account=account)
            db.commit()
            print(
                "Seeded local workspace for "
                f"{settings.owner_email} / {settings.owner_password.get_secret_value()}"
            )
        finally:
            db.close()
    except OperationalError as exc:
        message = (
            "Database connection failed while running seed_local_data.py. "
            "Start MySQL first or set DATABASE_URL/MYSQL_HOST for your current environment."
        )
        raise SystemExit(f"{message}\nOriginal error: {exc}") from exc


if __name__ == "__main__":
    main()
