"""Account management domain API.

Money is stored as integer cents. These functions are the import surface
for the CLI and for a future HTTP layer.
"""

from app.domain import (
    OPENING_BALANCE_CENTS,
    Account,
    AccountService,
    InsufficientFundsError,
    credit,
    debit,
    format_money,
    get_balance,
    parse_amount_to_cents,
)

__all__ = [
    "OPENING_BALANCE_CENTS",
    "Account",
    "AccountService",
    "InsufficientFundsError",
    "credit",
    "debit",
    "format_money",
    "get_balance",
    "parse_amount_to_cents",
]
