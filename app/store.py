"""JSON file persistence for account balance and a simple transaction ledger."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.domain import OPENING_BALANCE_CENTS

DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "balance.json"


@dataclass
class Transaction:
    amount_cents: int
    type: str
    timestamp: str
    resulting_balance_cents: int


@dataclass
class AccountState:
    balance_cents: int = OPENING_BALANCE_CENTS
    transactions: list[Transaction] = field(default_factory=list)


class JsonStore:
    """Load and save account state as JSON. Missing file → opening balance 1000.00."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_STORE_PATH

    def load(self) -> AccountState:
        if not self.path.exists():
            return AccountState()
        with self.path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        balance = int(raw["balance_cents"])
        transactions = [
            Transaction(
                amount_cents=int(item["amount_cents"]),
                type=str(item["type"]),
                timestamp=str(item["timestamp"]),
                resulting_balance_cents=int(item["resulting_balance_cents"]),
            )
            for item in raw.get("transactions", [])
        ]
        return AccountState(balance_cents=balance, transactions=transactions)

    def save(self, state: AccountState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "balance_cents": state.balance_cents,
            "transactions": [asdict(tx) for tx in state.transactions],
        }
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        tmp_path.replace(self.path)

    def load_balance_cents(self) -> int:
        return self.load().balance_cents

    def list_transactions(self) -> list[Transaction]:
        """Return ledger entries, oldest first. Missing file → empty list."""
        return list(self.load().transactions)

    def record_transaction(
        self,
        *,
        amount_cents: int,
        tx_type: str,
        resulting_balance_cents: int,
        timestamp: str,
    ) -> None:
        state = self.load()
        state.balance_cents = resulting_balance_cents
        state.transactions.append(
            Transaction(
                amount_cents=amount_cents,
                type=tx_type,
                timestamp=timestamp,
                resulting_balance_cents=resulting_balance_cents,
            )
        )
        self.save(state)


# Alias used by AccountService type hints.
BalanceStore = JsonStore
