from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TokenAllocationType, TokenWalletStatus
from app.models.token_ledger import TokenLedger
from app.models.token_wallet import TokenWallet
from app.schemas.billing import TokenBalanceBreakdown, TokenWalletResponse, WalletBalanceResponse


class TokenWalletService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_wallet(self, *, account: Account) -> TokenWallet:
        wallet = self.db.scalar(select(TokenWallet).where(TokenWallet.account_id == account.id))
        if wallet is None:
            wallet = TokenWallet(
                account_id=account.id,
                status=TokenWalletStatus.ACTIVE,
                balance_tokens=max(account.token_balance, 0),
                reserved_tokens=0,
                lifetime_credited_tokens=max(account.token_balance, 0),
                lifetime_debited_tokens=0,
                metadata_json={},
            )
            self.db.add(wallet)
            self.db.flush()
        return wallet

    def calculate_breakdown(self, *, wallet: TokenWallet) -> TokenBalanceBreakdown:
        now = self._utcnow()
        statement = select(
            TokenLedger.allocation_type,
            func.coalesce(func.sum(TokenLedger.remaining_tokens), 0),
        ).where(
            TokenLedger.token_wallet_id == wallet.id,
            TokenLedger.remaining_tokens.is_not(None),
            TokenLedger.remaining_tokens > 0,
            TokenLedger.is_expired.is_(False),
            ((TokenLedger.expires_at.is_(None)) | (TokenLedger.expires_at > now)),
        ).group_by(TokenLedger.allocation_type)
        rows = self.db.execute(statement).all()
        monthly = 0
        purchased = 0
        manual = 0
        for allocation_type, total in rows:
            amount = int(total or 0)
            if allocation_type == TokenAllocationType.MONTHLY_FREE:
                monthly = amount
            elif allocation_type == TokenAllocationType.PURCHASED:
                purchased = amount
            elif allocation_type == TokenAllocationType.MANUAL:
                manual = amount
        expiring_next_tokens = self.db.scalar(
            select(func.coalesce(func.sum(TokenLedger.remaining_tokens), 0)).where(
                TokenLedger.token_wallet_id == wallet.id,
                TokenLedger.allocation_type == TokenAllocationType.MONTHLY_FREE,
                TokenLedger.remaining_tokens.is_not(None),
                TokenLedger.remaining_tokens > 0,
                TokenLedger.is_expired.is_(False),
                TokenLedger.expires_at.is_not(None),
                TokenLedger.expires_at <= now + timedelta(days=7),
            )
        ) or 0
        return TokenBalanceBreakdown(
            available_monthly_free_tokens=monthly,
            available_purchased_tokens=purchased,
            available_manual_tokens=manual,
            total_available_tokens=monthly + purchased + manual,
            expiring_next_tokens=int(expiring_next_tokens),
        )

    def sync_account_balance(self, *, account: Account, wallet: TokenWallet) -> WalletBalanceResponse:
        breakdown = self.calculate_breakdown(wallet=wallet)
        wallet.balance_tokens = breakdown.total_available_tokens
        account.token_balance = breakdown.total_available_tokens
        self.db.flush()
        return WalletBalanceResponse(wallet=TokenWalletResponse.model_validate(wallet), breakdown=breakdown)

    def get_wallet_balance(self, *, account: Account) -> WalletBalanceResponse:
        wallet = self.ensure_wallet(account=account)
        return self.sync_account_balance(account=account, wallet=wallet)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
