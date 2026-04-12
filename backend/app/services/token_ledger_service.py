from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_subscription import AccountSubscription
from app.models.billing_transaction import BillingTransaction
from app.models.enums import (
    TokenAllocationType,
    TokenLedgerEntryType,
    TokenLedgerSourceType,
)
from app.models.token_ledger import TokenLedger
from app.models.token_wallet import TokenWallet
from app.services.token_wallet_service import TokenWalletService


class TokenLedgerService:
    def __init__(self, db: Session):
        self.db = db
        self.wallets = TokenWalletService(db)

    def credit_monthly_free_tokens(
        self,
        *,
        account: Account,
        amount: int,
        subscription: AccountSubscription | None = None,
        notes: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> TokenLedger:
        return self._create_credit_entry(
            account=account,
            amount=amount,
            allocation_type=TokenAllocationType.MONTHLY_FREE,
            source_type=TokenLedgerSourceType.SUBSCRIPTION,
            subscription=subscription,
            billing_transaction=None,
            notes=notes or "Monthly plan token credit.",
            metadata_json=metadata_json,
            expires_at=self._utcnow() + timedelta(days=30),
        )

    def credit_token_purchase(
        self,
        *,
        account: Account,
        amount: int,
        billing_transaction: BillingTransaction,
        notes: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> TokenLedger:
        return self._create_credit_entry(
            account=account,
            amount=amount,
            allocation_type=TokenAllocationType.PURCHASED,
            source_type=TokenLedgerSourceType.TOKEN_PACKAGE,
            subscription=None,
            billing_transaction=billing_transaction,
            notes=notes or "Purchased token package credit.",
            metadata_json=metadata_json,
            expires_at=None,
        )

    def manual_adjustment(
        self,
        *,
        account: Account,
        delta_tokens: int,
        notes: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> TokenLedger:
        if delta_tokens == 0:
            raise ValueError("delta_tokens must not be zero.")
        if delta_tokens > 0:
            return self._create_credit_entry(
                account=account,
                amount=delta_tokens,
                allocation_type=TokenAllocationType.MANUAL,
                source_type=TokenLedgerSourceType.ADMIN,
                subscription=None,
                billing_transaction=None,
                notes=notes or "Manual token adjustment.",
                metadata_json=metadata_json,
                expires_at=None,
            )
        wallet = self.wallets.ensure_wallet(account=account)
        balance_before = wallet.balance_tokens
        wallet.balance_tokens = max(wallet.balance_tokens + delta_tokens, 0)
        wallet.lifetime_debited_tokens += abs(delta_tokens)
        entry = TokenLedger(
            token_wallet_id=wallet.id,
            account_id=account.id,
            entry_type=TokenLedgerEntryType.ADJUSTMENT,
            source_type=TokenLedgerSourceType.ADMIN,
            allocation_type=TokenAllocationType.MANUAL,
            delta_tokens=delta_tokens,
            balance_before=balance_before,
            balance_after=wallet.balance_tokens,
            remaining_tokens=None,
            unit_price_usd=None,
            total_price_usd=None,
            notes=notes,
            occurred_at=self._utcnow(),
            metadata_json=metadata_json or {},
        )
        self.db.add(entry)
        self.wallets.sync_account_balance(account=account, wallet=wallet)
        self.db.flush()
        return entry

    def expire_tokens(self, *, account: Account | None = None) -> int:
        now = self._utcnow()
        statement = select(TokenLedger).where(
            TokenLedger.entry_type == TokenLedgerEntryType.CREDIT,
            TokenLedger.remaining_tokens.is_not(None),
            TokenLedger.remaining_tokens > 0,
            TokenLedger.expires_at.is_not(None),
            TokenLedger.expires_at <= now,
            TokenLedger.is_expired.is_(False),
        )
        if account is not None:
            statement = statement.where(TokenLedger.account_id == account.id)
        credits = self.db.scalars(statement.order_by(TokenLedger.expires_at.asc(), TokenLedger.id.asc())).all()
        expired = 0
        wallet_cache: dict[int, TokenWallet] = {}
        account_cache: dict[int, Account] = {}
        for credit in credits:
            if not credit.remaining_tokens:
                continue
            wallet = wallet_cache.get(credit.token_wallet_id)
            if wallet is None:
                wallet = self.db.get(TokenWallet, credit.token_wallet_id)
                if wallet is None:
                    continue
                wallet_cache[credit.token_wallet_id] = wallet
            account_row = account_cache.get(credit.account_id)
            if account_row is None:
                account_row = account or self.db.get(Account, credit.account_id)
                if account_row is None:
                    continue
                account_cache[credit.account_id] = account_row
            amount = credit.remaining_tokens
            balance_before = wallet.balance_tokens
            wallet.balance_tokens = max(wallet.balance_tokens - amount, 0)
            wallet.lifetime_debited_tokens += amount
            credit.remaining_tokens = 0
            credit.is_expired = True
            credit.expired_at = now
            self.db.add(
                TokenLedger(
                    token_wallet_id=wallet.id,
                    account_id=credit.account_id,
                    account_subscription_id=credit.account_subscription_id,
                    billing_transaction_id=credit.billing_transaction_id,
                    entry_type=TokenLedgerEntryType.EXPIRE,
                    source_type=TokenLedgerSourceType.EXPIRATION,
                    allocation_type=credit.allocation_type,
                    delta_tokens=-amount,
                    balance_before=balance_before,
                    balance_after=wallet.balance_tokens,
                    remaining_tokens=None,
                    expires_at=credit.expires_at,
                    expired_at=now,
                    is_expired=True,
                    unit_price_usd=credit.unit_price_usd,
                    total_price_usd=Decimal("0"),
                    reference_type="token_ledger",
                    reference_id=str(credit.id),
                    notes="Expired monthly free tokens.",
                    occurred_at=now,
                    metadata_json={"expired_credit_entry_id": credit.id},
                )
            )
            self.wallets.sync_account_balance(account=account_row, wallet=wallet)
            expired += amount
        self.db.flush()
        return expired

    def list_entries(self, *, account: Account) -> list[TokenLedger]:
        return self.db.scalars(
            select(TokenLedger)
            .where(TokenLedger.account_id == account.id)
            .order_by(TokenLedger.occurred_at.desc(), TokenLedger.id.desc())
        ).all()

    def _create_credit_entry(
        self,
        *,
        account: Account,
        amount: int,
        allocation_type: TokenAllocationType,
        source_type: TokenLedgerSourceType,
        subscription: AccountSubscription | None,
        billing_transaction: BillingTransaction | None,
        notes: str | None,
        metadata_json: dict[str, Any] | None,
        expires_at: datetime | None,
    ) -> TokenLedger:
        wallet = self.wallets.ensure_wallet(account=account)
        balance_before = wallet.balance_tokens
        wallet.balance_tokens += amount
        wallet.lifetime_credited_tokens += amount
        entry = TokenLedger(
            token_wallet_id=wallet.id,
            account_id=account.id,
            account_subscription_id=subscription.id if subscription else None,
            billing_transaction_id=billing_transaction.id if billing_transaction else None,
            entry_type=TokenLedgerEntryType.CREDIT,
            source_type=source_type,
            allocation_type=allocation_type,
            delta_tokens=amount,
            balance_before=balance_before,
            balance_after=wallet.balance_tokens,
            remaining_tokens=amount,
            expires_at=expires_at,
            expired_at=None,
            is_expired=False,
            unit_price_usd=None,
            total_price_usd=None,
            notes=notes,
            occurred_at=self._utcnow(),
            metadata_json=metadata_json or {},
        )
        self.db.add(entry)
        self.wallets.sync_account_balance(account=account, wallet=wallet)
        self.db.flush()
        return entry

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
