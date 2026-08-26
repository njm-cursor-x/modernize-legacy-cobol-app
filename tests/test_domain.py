"""Domain tests mapped to TESTPLAN.md plus invalid-input cases."""

import pytest

from app.domain import (
    OPENING_BALANCE_CENTS,
    Account,
    InsufficientFundsError,
    credit,
    debit,
    format_money,
    get_balance,
    parse_amount_to_cents,
)


def test_tc_1_1_view_current_balance():
    account = Account()
    assert get_balance(account) == OPENING_BALANCE_CENTS
    assert format_money(get_balance(account)) == "$1,000.00"


def test_tc_2_1_credit_valid():
    account = Account()
    new_balance = credit(account, 10_000)  # $100.00
    assert new_balance == 110_000
    assert get_balance(account) == 110_000
    assert format_money(new_balance) == "$1,100.00"


def test_tc_2_2_credit_zero():
    account = Account()
    new_balance = credit(account, 0)
    assert new_balance == OPENING_BALANCE_CENTS
    assert get_balance(account) == OPENING_BALANCE_CENTS


def test_tc_3_1_debit_valid():
    account = Account()
    new_balance = debit(account, 5_000)  # $50.00
    assert new_balance == 95_000
    assert get_balance(account) == 95_000
    assert format_money(new_balance) == "$950.00"


def test_tc_3_2_debit_greater_than_balance_insufficient_funds():
    account = Account()
    with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
        debit(account, 200_000)  # $2,000.00
    assert get_balance(account) == OPENING_BALANCE_CENTS


def test_tc_3_3_debit_zero():
    account = Account()
    new_balance = debit(account, 0)
    assert new_balance == OPENING_BALANCE_CENTS
    assert get_balance(account) == OPENING_BALANCE_CENTS


def test_credit_always_applies():
    account = Account()
    credit(account, 1)
    credit(account, 0)
    credit(account, 99)
    assert get_balance(account) == OPENING_BALANCE_CENTS + 100


def test_debit_equal_to_balance_allowed():
    account = Account()
    debit(account, OPENING_BALANCE_CENTS)
    assert get_balance(account) == 0


def test_reject_negative_credit():
    account = Account()
    with pytest.raises(ValueError):
        credit(account, -1)
    assert get_balance(account) == OPENING_BALANCE_CENTS


def test_reject_negative_debit():
    account = Account()
    with pytest.raises(ValueError):
        debit(account, -50)
    assert get_balance(account) == OPENING_BALANCE_CENTS


def test_reject_non_integer_amounts():
    account = Account()
    with pytest.raises(TypeError):
        credit(account, 10.00)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        debit(account, True)  # type: ignore[arg-type]


def test_parse_amount_valid():
    assert parse_amount_to_cents("100.00") == 10_000
    assert parse_amount_to_cents("100") == 10_000
    assert parse_amount_to_cents("100.0") == 10_000
    assert parse_amount_to_cents("0.00") == 0
    assert parse_amount_to_cents(" 50.5 ") == 5_050


def test_parse_amount_rejects_negatives_and_non_numeric():
    for raw in ("-1", "-100.00", "abc", "", "  ", "100.001", "1,000.00", "$100.00", "+10"):
        with pytest.raises(ValueError):
            parse_amount_to_cents(raw)


def test_format_money_thousands():
    assert format_money(115_000) == "$1,150.00"
    assert format_money(0) == "$0.00"
