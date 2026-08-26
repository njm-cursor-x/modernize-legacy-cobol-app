"""Persistence tests. Use tmp_path so demo data is never clobbered."""

from app.domain import OPENING_BALANCE_CENTS, AccountService, InsufficientFundsError
from app.store import JsonStore


def test_missing_file_defaults_to_opening_balance(tmp_path):
    path = tmp_path / "balance.json"
    store = JsonStore(path)
    assert store.load_balance_cents() == OPENING_BALANCE_CENTS
    assert not path.exists()


def test_persistence_round_trip(tmp_path):
    path = tmp_path / "balance.json"
    service = AccountService(JsonStore(path))
    service.credit(10_000)
    service.debit(5_000)

    restarted = AccountService(JsonStore(path))
    assert restarted.get_balance() == 105_000

    state = JsonStore(path).load()
    assert len(state.transactions) == 2
    assert state.transactions[0].type == "credit"
    assert state.transactions[0].amount_cents == 10_000
    assert state.transactions[0].resulting_balance_cents == 110_000
    assert state.transactions[1].type == "debit"
    assert state.transactions[1].amount_cents == 5_000
    assert state.transactions[1].resulting_balance_cents == 105_000


def test_insufficient_funds_does_not_write(tmp_path):
    path = tmp_path / "balance.json"
    service = AccountService(JsonStore(path))
    service.credit(100)

    try:
        service.debit(200_000)
    except InsufficientFundsError:
        pass
    else:
        raise AssertionError("expected InsufficientFundsError")

    restarted = AccountService(JsonStore(path))
    assert restarted.get_balance() == OPENING_BALANCE_CENTS + 100
    assert len(JsonStore(path).load().transactions) == 1


def test_restart_does_not_reset_existing_file(tmp_path):
    path = tmp_path / "data" / "balance.json"
    first = AccountService(JsonStore(path))
    first.credit(15_000)
    second = AccountService(JsonStore(path))
    assert second.get_balance() == 115_000
