# Bug-test report — pass 2

Pass number: **2**

Status: **PASS**

No application code, tests, or seeds were modified. No re-seed. Bandit was not run.

## Command lines

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
printf '1\n4\n' | python3 -m app.cli
```

Environment: Python 3.12.3, pytest 9.1.1, cwd `/workspace`.

`pip install` reported packages already satisfied (`fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `pytest>=8.0` → 9.1.1, `httpx>=0.27`).

Bandit / pip-audit were **not** run.

## Summary

| Metric | Count |
| --- | ---: |
| collected | 34 |
| passed | 34 |
| failed | 0 |
| errors | 0 |
| skipped | 0 |

Pytest footer: `34 passed, 1 warning in 0.36s`

Warning (non-failing): StarletteDeprecationWarning from `fastapi/testclient.py` — `Using httpx with starlette.testclient is deprecated; install httpx2 instead.`

## DELTA vs pass 1 (`reports/bugs/pass-1.md`)

Pass 1 original run: **24 collected, 19 passed, 5 failed, 0 errors** (seeded functional bugs). After a later test-only fix recorded in the same file, pass 1 was **24 passed**.

Pass 2: **34 collected, 34 passed, 0 failed, 0 errors**.

| Area | Pass 1 (original FAIL) | Pass 2 |
| --- | --- | --- |
| collected | 24 | 34 (+10 web tests in `tests/test_web.py`) |
| passed | 19 | 34 |
| failed | 5 | 0 |
| errors | 0 | 0 |

### Seeded functional bugs — absent in pass 2

The five pass-1 failures are gone. Domain/store/CLI regressions did **not** reappear:

| Pass 1 failure | Pass 2 result |
| --- | --- |
| `tests/test_cli.py::test_credit_debit_and_insufficient_funds_via_cli` (debit ignored prior credit; overdraft allowed) | **PASSED** |
| `tests/test_domain.py::test_tc_3_2_debit_greater_than_balance_insufficient_funds` (`InsufficientFundsError` not raised) | **PASSED** |
| `tests/test_store.py::test_persistence_round_trip` (credit did not persist) | **PASSED** |
| `tests/test_store.py::test_insufficient_funds_does_not_write` (debit overdrew instead of refusing) | **PASSED** |
| `tests/test_store.py::test_restart_does_not_reset_existing_file` (credit not saved across restart) | **PASSED** |

No new domain/store/CLI failures. All pre-existing CLI and domain tests that passed in pass 1 still pass.

### New UI-only tests vs domain regressions

The +10 collected tests are **web/UI HTTP tests** (`tests/test_web.py`), not new domain regressions. All 10 passed. There are **no UI-only failures** and **no domain regressions**.

New coverage in this pass (all PASSED): HTML opening balance, JSON balance API, HTML credit/debit, insufficient-funds HTML, zero amounts, JSON credit/debit/409, invalid amount 400, transaction list, tmp-store isolation.

## Web tests (`tests/test_web.py`)

All HTTP tests were collected and run.

| Test | Result |
| --- | --- |
| `tests/test_web.py::test_opening_balance_html` | PASSED |
| `tests/test_web.py::test_opening_balance_json` | PASSED |
| `tests/test_web.py::test_credit_100_then_new_balance` | PASSED |
| `tests/test_web.py::test_debit_50` | PASSED |
| `tests/test_web.py::test_debit_2000_insufficient_funds_balance_unchanged` | PASSED |
| `tests/test_web.py::test_zero_credit_and_debit_allowed` | PASSED |
| `tests/test_web.py::test_credit_debit_flow_json` | PASSED |
| `tests/test_web.py::test_invalid_amount_re_renders_with_error` | PASSED |
| `tests/test_web.py::test_transactions_listed_after_credit` | PASSED |
| `tests/test_web.py::test_web_tests_do_not_touch_default_store` | PASSED |

**10/10 web tests passed.**

## Remaining pytest results (non-web)

All CLI, domain, and store tests passed (24/24). Combined with web: 34/34.

## CLI smoke

Command:

```bash
printf '1\n4\n' | python3 -m app.cli
```

Process exit code: `0`

```
--------------------------------
Account Management System
1. View Balance
2. Credit Account
3. Debit Account
4. Exit
--------------------------------
Enter your choice (1-4):
Current balance: $1,050.00
--------------------------------
Account Management System
1. View Balance
2. Credit Account
3. Debit Account
4. Exit
--------------------------------
Enter your choice (1-4):
Exiting the program. Goodbye!
```

View-balance + exit succeeded. Balance `$1,050.00` is from existing `data/balance.json` (left by prior sessions). Pytest uses `tmp_path` / isolated stores and is independent of this file.

## Status

**PASS** — collected 34, passed 34, failed 0, errors 0. Seeded functional bugs from pass 1 are absent. No new UI-only failures. No domain regressions. Web HTTP suite 10/10 passed.
