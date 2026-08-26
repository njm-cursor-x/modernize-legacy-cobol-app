# Account Management System

Python replacement of a small GnuCOBOL account program. The original COBOL sources are archived under `legacy/` and are unchanged.

The Python app keeps the same menu and rules: opening balance **$1,000.00**, credit always applies, debit is refused when the amount is greater than the balance (`Insufficient funds`), zero amounts are allowed. Money is stored as **integer cents** (no floating-point arithmetic). Balance is persisted in `data/balance.json` so a restart does not reset an existing file.

## Run the Python app

Python 3.11+; standard library only for the CLI.

```bash
python -m app.cli
```

`python -m app` starts the same CLI.

```
--------------------------------
Account Management System
1. View Balance
2. Credit Account
3. Debit Account
4. Exit
--------------------------------
Enter your choice (1-4):
```

Balances are printed as `$1,150.00` (not COBOL-style leading zeros).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Cases follow `TESTPLAN.md` (view, credit, debit, insufficient funds, exit) plus invalid input and persistence round-trips. Store tests use pytest `tmp_path` so they never write over demo data.

## Legacy COBOL

Sources live in `legacy/` (`main.cob`, `operations.cob`, `data.cob`). Compile and run:

```bash
cobc -x main.cob operations.cob data.cob -o accountsystem
./accountsystem
```

See `legacy/README.md`.

## Layout

| Path | Role |
|------|------|
| `app/domain.py` | view / credit / debit; importable by a future HTTP layer |
| `app/store.py` | JSON persistence and transaction ledger |
| `app/cli.py` | interactive menu |
| `legacy/` | archived COBOL |
| `TESTPLAN.md` | original business-logic test plan |

## License

MIT. See [LICENSE](LICENSE).
