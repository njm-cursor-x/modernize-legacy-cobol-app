# Seeded findings — pass 1 (demo-only)

Planted by the Phase 1b seed agent. These are intentional, allowlisted demo defects so later test and scan passes have real findings. **Not production issues.** Tests under `tests/` were not modified and remain the spec.

Shuffle order used:

- Functional allowlist shuffled to `[2, 1, 3]` → picked **2** and **1** (skipped opening-balance).
- SAST allowlist shuffled to `[4, 1, 3, 2, 5]` → picked **4**, **1**, and **3** (skipped hardcoded secret and debug leftovers).
- SCA pin is mandatory and was included.

## Functional bugs (pytest / TESTPLAN must fail)

| # | What | Location | Detector | Demo-only |
| --- | --- | --- | --- | --- |
| 1 | **Debit skips the insufficient-funds check** (`Account.debit` subtracts without refusing overdraft). | `app/domain.py:49` | pytest `test_tc_3_2_debit_greater_than_balance_insufficient_funds` (TESTPLAN **TC-3.2**); also `tests/test_store.py::test_insufficient_funds_does_not_write`; CLI session `tests/test_cli.py::test_credit_debit_and_insufficient_funds_via_cli` | yes |
| 2 | **Credit does not persist** (`AccountService.credit` computes the in-memory balance and returns it, but never calls `record_transaction` / save). | `app/domain.py:126-129` | pytest `tests/test_store.py::test_persistence_round_trip`; `tests/test_store.py::test_restart_does_not_reset_existing_file`; CLI session also fails after a credit because the following debit reloads the unsaved store | yes |

Not planted: opening balance still `1000.00` (`OPENING_BALANCE_CENTS = 100_000`).

## SAST (Bandit)

Unused support helpers in `app/admin.py` (not imported by the CLI or pytest happy path). Collection still works.

| # | What | Location | Detector | Demo-only |
| --- | --- | --- | --- | --- |
| 1 | **`eval()`** on a leftover ops formula helper | `app/admin.py:14` | Bandit **B307** (`blacklist` / use of `eval`) | yes |
| 2 | **`pickle.loads`** on a leftover snapshot restore helper | `app/admin.py:19` | Bandit **B301** (also **B403** on `import pickle` at `app/admin.py:5`) | yes |
| 3 | **`subprocess` with `shell=True`** on an unused backup-host ping | `app/admin.py:24` | Bandit **B602** (`subprocess_popen_with_shell_equals_true`; also **B404** on `import subprocess` at `app/admin.py:6`) | yes |

Not planted: hardcoded secret/token; debug leftovers (`DEBUG=True` / `assert True`).

## SCA + reachability (pip-audit)

| # | What | Location | Detector | Demo-only |
| --- | --- | --- | --- | --- |
| 1 | Pin **`requests==2.19.1`** and import it from a first-party app module | pin: `requirements.txt:2`; import: `app/admin.py:9` | pip-audit **PYSEC-2018-28** (`CVE-2018-18074`) and additional advisories on that pin (**PYSEC-2023-74** / `CVE-2023-32681`, **PYSEC-2026-1873** / `CVE-2024-35195`, **PYSEC-2026-1872** / `CVE-2024-47081`, **PYSEC-2026-2275** / `CVE-2026-25645`); import-graph **reachable** | yes |

## Verification (then discarded)

`python3 .cursor/skills/vuln-reachability-scan/scripts/scan.py --pass 99 --root /workspace` reported **11** findings, all reachable, including **≥1 high reachable**:

- Bandit **B602: subprocess_popen_with_shell_equals_true** (`app/admin.py:24`) — **high**, reachable
- Bandit B307 / B301 — medium, reachable
- pip-audit PYSEC-2018-28 and other `requests==2.19.1` advisories — reachable (severity `unknown` in this runner because the advisory JSON has no CVSS)

`reports/security/pass-99.*` were deleted after this check so they do not pollute pass-1.

## Pytest after seeds

`5 failed, 19 passed`. Tests under `tests/` were not edited.
