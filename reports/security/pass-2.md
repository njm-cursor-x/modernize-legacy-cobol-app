# Vulnerability reachability scan — pass 2

Generated: `2026-08-26T14:27:48Z`

Reachability is **module-level** (static imports in `app/`). This is not function-level or commercial reachability.

## Scanners

| Name | Version | Command |
| --- | --- | --- |
| bandit | bandit 1.9.4 | `/home/ubuntu/.local/bin/bandit -r /workspace/app -x .venv,venv,__pycache__ -f json -q -o /tmp/vuln-reach-ccz3yx5v/bandit.json` |
| pip-audit | pip-audit 2.10.1 | `/home/ubuntu/.local/bin/pip-audit -r /workspace/requirements.txt -f json --progress-spinner off --no-deps --disable-pip -o /tmp/vuln-reach-ccz3yx5v/pip-audit.json` |

## Summary by severity

| Severity | Count |
| --- | ---: |
| critical | 0 |
| high | 0 |
| medium | 0 |
| low | 0 |
| unknown | 0 |
| **total** | **0** |

## Summary by reachability

| Reachability | Count |
| --- | ---: |
| reachable | 0 |
| unreachable | 0 |
| unknown | 0 |
| n/a | 0 |

## Findings

No findings.

## Comparison vs pass 1

Pass 1 had **11** findings (all reachable). Pass 2 has **0**. No High/Critical reachable findings remain.

### Pass-1 finding IDs — all resolved (gone)

`app/admin.py` was removed and `requests` was not re-added to `requirements.txt`. None of these IDs appear in pass-2.json.

| Pass-1 ID | Source | Why gone |
| --- | --- | --- |
| `bandit:B403:app/admin.py:5` | bandit | `app/admin.py` deleted (pickle import) |
| `bandit:B404:app/admin.py:6` | bandit | `app/admin.py` deleted (subprocess import) |
| `bandit:B307:app/admin.py:14` | bandit | `app/admin.py` deleted (`eval`) |
| `bandit:B301:app/admin.py:19` | bandit | `app/admin.py` deleted (`pickle.loads`) |
| `bandit:B602:app/admin.py:24` | bandit | `app/admin.py` deleted (`subprocess` `shell=True`) |
| `pip-audit:PYSEC-2018-28:requests` | pip-audit | `requests` not in runtime pins |
| `pip-audit:PYSEC-2023-74:requests` | pip-audit | `requests` not in runtime pins (first advisory) |
| `pip-audit:PYSEC-2023-74:requests` | pip-audit | `requests` not in runtime pins (duplicate advisory) |
| `pip-audit:PYSEC-2026-1873:requests` | pip-audit | `requests` not in runtime pins |
| `pip-audit:PYSEC-2026-1872:requests` | pip-audit | `requests` not in runtime pins |
| `pip-audit:PYSEC-2026-2275:requests` | pip-audit | `requests` not in runtime pins |

**11/11 resolved.**

### New frontend / runtime deps vs pip-audit

Pinned in `requirements.txt` for `--no-deps --disable-pip`. pytest is only in `requirements-dev.txt`.

| Package | Pin | Imported by `app/` | pip-audit flagged? |
| --- | --- | --- | --- |
| fastapi | `0.141.1` | yes (`app/web.py`) | no |
| uvicorn | `0.52.4` | CLI only (`uvicorn app.web:app`) | no |
| jinja2 | `3.1.6` | used via FastAPI `Jinja2Templates` | no |
| python-multipart | `0.0.32` | used via FastAPI `Form(...)` | no |
| pydantic | `2.13.4` | yes (`app/web.py`) | no |

pip-audit ran against these exact pins and reported **zero** vulnerabilities.

### New Bandit hits in `web.py`

**None.** Bandit scanned `app/` (including `app/web.py`) and returned no issues. Pass 1 Bandit hits were all in `app/admin.py`, which is gone.
