from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TokenLedgerEntryType, TokenLedgerSourceType
from app.models.token_ledger import TokenLedger
from app.services.token_wallet_service import TokenWalletService


class TokenConsumptionService:
    def __init__(self, db: Session):
        self.db = db
        self.wallets = TokenWalletService(db)

    def debit_tokens(
        self,
        *,
        account: Account,
        amount: int,
        reference_type: str,
        reference_id: str | None,
        source_type: TokenLedgerSourceType = TokenLedgerSourceType.AI_USAGE,
        notes: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> TokenLedger:
        if amount <= 0:
            raise ValueError("amount must be positive.")
        wallet = self.wallets.ensure_wallet(account=account)
        balance = self.wallets.calculate_breakdown(wallet=wallet)
        debit_amount = min(amount, balance.total_available_tokens)
        if debit_amount <= 0:
            debit = TokenLedger(
                token_wallet_id=wallet.id,
                account_id=account.id,
                entry_type=TokenLedgerEntryType.DEBIT,
                source_type=source_type,
                allocation_type=None,
                delta_tokens=0,
                balance_before=wallet.balance_tokens,
                balance_after=wallet.balance_tokens,
                remaining_tokens=None,
                expires_at=None,
                expired_at=None,
                is_expired=False,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes,
                occurred_at=self._utcnow(),
                metadata_json={**(metadata_json or {}), "allocations": [], "requested_tokens": amount, "debited_tokens": 0},
            )
            self.db.add(debit)
            self.db.flush()
            return debit

        now = self._utcnow()
        credits = self.db.scalars(
            select(TokenLedger)
            .where(
                TokenLedger.token_wallet_id == wallet.id,
                TokenLedger.entry_type == TokenLedgerEntryType.CREDIT,
                TokenLedger.remaining_tokens.is_not(None),
                TokenLedger.remaining_tokens > 0,
                TokenLedger.is_expired.is_(False),
                ((TokenLedger.expires_at.is_(None)) | (TokenLedger.expires_at > now)),
            )
            .order_by(
                case((TokenLedger.expires_at.is_(None), 1), else_=0).asc(),
                TokenLedger.expires_at.asc().nullslast(),
                TokenLedger.created_at.asc(),
                TokenLedger.id.asc(),
            )
        ).all()

        remaining = debit_amount
        allocations: list[dict[str, Any]] = []
        for credit in credits:
            if remaining <= 0:
                break
            available = int(credit.remaining_tokens or 0)
            if available <= 0:
                continue
            consume = min(available, remaining)
            credit.remaining_tokens = available - consume
            allocations.append(
                {
                    "credit_entry_id": credit.id,
                    "allocation_type": credit.allocation_type.value if credit.allocation_type else None,
                    "consumed_tokens": consume,
                    "expires_at": credit.expires_at.isoformat() if credit.expires_at else None,
                }
            )
            remaining -= consume
        if remaining > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to allocate token debit cleanly.")

        balance_before = wallet.balance_tokens
        wallet.balance_tokens = max(wallet.balance_tokens - debit_amount, 0)
        wallet.lifetime_debited_tokens += debit_amount
        debit = TokenLedger(
            token_wallet_id=wallet.id,
            account_id=account.id,
            entry_type=TokenLedgerEntryType.DEBIT,
            source_type=source_type,
            allocation_type=None,
            delta_tokens=-debit_amount,
            balance_before=balance_before,
            balance_after=wallet.balance_tokens,
            remaining_tokens=None,
            expires_at=None,
            expired_at=None,
            is_expired=False,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            occurred_at=now,
            metadata_json={**(metadata_json or {}), "allocations": allocations, "requested_tokens": amount, "debited_tokens": debit_amount},
        )
        self.db.add(debit)
        self.wallets.sync_account_balance(account=account, wallet=wallet)
        self.db.flush()
        return debit

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
