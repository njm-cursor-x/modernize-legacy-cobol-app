"""Interactive account-management CLI (same menu as the archived COBOL program)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, Optional

from app.domain import AccountService, InsufficientFundsError, format_money, parse_amount_to_cents
from app.store import DEFAULT_STORE_PATH, JsonStore

MENU = """--------------------------------
Account Management System
1. View Balance
2. Credit Account
3. Debit Account
4. Exit
--------------------------------
Enter your choice (1-4):"""

EXIT_MESSAGE = "Exiting the program. Goodbye!"
INVALID_CHOICE = "Invalid choice, please select 1-4."


def run(
    stdin: Optional[IO[str]] = None,
    stdout: Optional[IO[str]] = None,
    store_path: Optional[Path] = None,
) -> None:
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    service = AccountService(JsonStore(store_path or DEFAULT_STORE_PATH))

    while True:
        _write(stdout, MENU)
        choice = _read_line(stdin)
        if choice is None:
            break
        choice = choice.strip()

        if choice == "1":
            _write(stdout, f"Current balance: {format_money(service.get_balance())}")
        elif choice == "2":
            _credit(service, stdin, stdout)
        elif choice == "3":
            _debit(service, stdin, stdout)
        elif choice == "4":
            break
        else:
            _write(stdout, INVALID_CHOICE)

    _write(stdout, EXIT_MESSAGE)


def _credit(service: AccountService, stdin: IO[str], stdout: IO[str]) -> None:
    amount = _read_amount(stdin, stdout, "Enter credit amount: ")
    if amount is None:
        return
    new_balance = service.credit(amount)
    _write(stdout, f"Amount credited. New balance: {format_money(new_balance)}")


def _debit(service: AccountService, stdin: IO[str], stdout: IO[str]) -> None:
    amount = _read_amount(stdin, stdout, "Enter debit amount: ")
    if amount is None:
        return
    try:
        new_balance = service.debit(amount)
    except InsufficientFundsError as exc:
        _write(stdout, str(exc))
        return
    _write(stdout, f"Amount debited. New balance: {format_money(new_balance)}")


def _read_amount(stdin: IO[str], stdout: IO[str], prompt: str) -> Optional[int]:
    _write(stdout, prompt)
    line = _read_line(stdin)
    if line is None:
        return None
    try:
        return parse_amount_to_cents(line)
    except ValueError:
        _write(stdout, "Invalid amount. Please enter a non-negative number.")
        return None


def _read_line(stdin: IO[str]) -> Optional[str]:
    line = stdin.readline()
    if line == "":
        return None
    return line.rstrip("\n")


def _write(stdout: IO[str], text: str) -> None:
    stdout.write(text + "\n")
    stdout.flush()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
