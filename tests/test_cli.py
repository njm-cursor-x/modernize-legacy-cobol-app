"""CLI tests: TESTPLAN TC-4.1, menu copy, invalid input, and a full session."""

from io import StringIO

from app.cli import EXIT_MESSAGE, INVALID_CHOICE, MENU, run


def _run_session(lines: str, store_path) -> str:
    stdin = StringIO(lines)
    stdout = StringIO()
    run(stdin=stdin, stdout=stdout, store_path=store_path)
    return stdout.getvalue()


def test_tc_4_1_exit(tmp_path):
    output = _run_session("4\n", tmp_path / "balance.json")
    assert MENU.splitlines()[1] in output
    assert "Account Management System" in output
    assert EXIT_MESSAGE in output


def test_invalid_choice_rejected(tmp_path):
    output = _run_session("9\n4\n", tmp_path / "balance.json")
    assert INVALID_CHOICE in output
    assert EXIT_MESSAGE in output


def test_tc_1_1_view_balance_via_cli(tmp_path):
    output = _run_session("1\n4\n", tmp_path / "balance.json")
    assert "Current balance: $1,000.00" in output


def test_credit_debit_and_insufficient_funds_via_cli(tmp_path):
    output = _run_session(
        "1\n2\n100.00\n3\n50.00\n3\n2000.00\n4\n",
        tmp_path / "balance.json",
    )
    assert "Current balance: $1,000.00" in output
    assert "Amount credited. New balance: $1,100.00" in output
    assert "Amount debited. New balance: $1,050.00" in output
    assert "Insufficient funds" in output
    assert EXIT_MESSAGE in output


def test_cli_rejects_negative_and_non_numeric_amounts(tmp_path):
    output = _run_session("2\n-10\n2\nabc\n3\n-1\n3\nxyz\n4\n", tmp_path / "balance.json")
    assert output.count("Invalid amount") == 4
    assert "Amount credited" not in output
    assert "Amount debited" not in output


def test_menu_matches_cobol():
    expected = """--------------------------------
Account Management System
1. View Balance
2. Credit Account
3. Debit Account
4. Exit
--------------------------------
Enter your choice (1-4):"""
    assert MENU == expected
