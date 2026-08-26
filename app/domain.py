"""Account operations: view, credit, debit.

All money arithmetic uses integer cents. Never use float for balances.
Opening balance is 1000.00 (100_000 cents).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.store import BalanceStore

OPENING_BALANCE_CENTS = 100_000  # $1,000.00

_AMOUNT_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")


class InsufficientFundsError(Exception):
    """Debit refused because the amount is greater than the current balance."""

    def __init__(self, message: str = "Insufficient funds for this debit.") -> None:
        super().__init__(message)


class Account:
    """In-memory account. Balance is always integer cents."""

    def __init__(self, balance_cents: int = OPENING_BALANCE_CENTS) -> None:
        if not isinstance(balance_cents, int) or isinstance(balance_cents, bool):
            raise TypeError("balance_cents must be an int")
        if balance_cents < 0:
            raise ValueError("balance_cents cannot be negative")
        self._balance_cents = balance_cents

    @property
    def balance_cents(self) -> int:
        return self._balance_cents

    def credit(self, amount_cents: int) -> int:
        _require_non_negative_cents(amount_cents)
        self._balance_cents += amount_cents
        return self._balance_cents

    def debit(self, amount_cents: int) -> int:
        _require_non_negative_cents(amount_cents)
        self._balance_cents -= amount_cents
        return self._balance_cents


def get_balance(account: Account) -> int:
    """Return the current balance in cents."""
    return account.balance_cents


def credit(account: Account, amount_cents: int) -> int:
    """Apply a credit. Zero is allowed; negatives are rejected. Returns new balance in cents."""
    return account.credit(amount_cents)


def debit(account: Account, amount_cents: int) -> int:
    """Apply a debit. Refuses (no write) when amount > balance. Returns new balance in cents."""
    return account.debit(amount_cents)


def format_money(cents: int) -> str:
    """Format integer cents as display currency, e.g. ``$1,150.00``."""
    if not isinstance(cents, int) or isinstance(cents, bool):
        raise TypeError("cents must be an int")
    sign = "-" if cents < 0 else ""
    absolute = abs(cents)
    dollars, remainder = divmod(absolute, 100)
    return f"{sign}${dollars:,}.{remainder:02d}"


def parse_amount_to_cents(text: str) -> int:
    """Parse a user-entered amount into integer cents.

    Accepts ``100``, ``100.0``, ``100.00``. Rejects negatives, empty input,
    non-numeric values, and more than two decimal places.
    """
    if text is None:
        raise ValueError("Amount must be a non-negative number")
    stripped = str(text).strip()
    if not _AMOUNT_PATTERN.match(stripped):
        raise ValueError("Amount must be a non-negative number with at most two decimal places")
    dollars_part, _, cents_part = stripped.partition(".")
    if not cents_part:
        cents_part = "00"
    elif len(cents_part) == 1:
        cents_part = cents_part + "0"
    return int(dollars_part) * 100 + int(cents_part)


def _require_non_negative_cents(amount_cents: int) -> None:
    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
        raise TypeError("amount_cents must be an int")
    if amount_cents < 0:
        raise ValueError("Amount must be non-negative")


class SupportsBalanceStore(Protocol):
    def load_balance_cents(self) -> int: ...

    def record_transaction(
        self,
        *,
        amount_cents: int,
        tx_type: str,
        resulting_balance_cents: int,
        timestamp: str,
    ) -> None: ...


class AccountService:
    """Persistence-backed view/credit/debit for the CLI or a future HTTP layer."""

    def __init__(self, store: BalanceStore | SupportsBalanceStore) -> None:
        self._store = store

    def get_balance(self) -> int:
        return self._store.load_balance_cents()

    def credit(self, amount_cents: int) -> int:
        account = Account(self._store.load_balance_cents())
        new_balance = credit(account, amount_cents)
        return new_balance

    def debit(self, amount_cents: int) -> int:
        account = Account(self._store.load_balance_cents())
        new_balance = debit(account, amount_cents)
        self._store.record_transaction(
            amount_cents=amount_cents,
            tx_type="debit",
            resulting_balance_cents=new_balance,
            timestamp=_now_iso(),
        )
        return new_balance


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
