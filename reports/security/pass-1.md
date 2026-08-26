# Vulnerability reachability scan — pass 1

Generated: `2026-08-26T14:09:34Z`

Reachability is **module-level** (static imports in `app/`). This is not function-level or commercial reachability.

## Scanners

| Name | Version | Command |
| --- | --- | --- |
| bandit | bandit 1.9.4 | `/home/ubuntu/.local/bin/bandit -r /workspace/app -x .venv,venv,__pycache__ -f json -q -o /tmp/vuln-reach-nui88hxw/bandit.json` |
| pip-audit | pip-audit 2.10.1 | `/home/ubuntu/.local/bin/pip-audit -r /workspace/requirements.txt -f json --progress-spinner off --no-deps --disable-pip -o /tmp/vuln-reach-nui88hxw/pip-audit.json` |

## Summary by severity

| Severity | Count |
| --- | ---: |
| critical | 0 |
| high | 1 |
| medium | 2 |
| low | 2 |
| unknown | 6 |
| **total** | **11** |

## Summary by reachability

| Reachability | Count |
| --- | ---: |
| reachable | 11 |
| unreachable | 0 |
| unknown | 0 |
| n/a | 0 |

## Findings

| ID | Source | Package | CVE | Severity | Reachability | Location | Title |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bandit:B403:app/admin.py:5 | bandit |  |  | low | reachable | app/admin.py:5 | B403: blacklist |
| bandit:B404:app/admin.py:6 | bandit |  |  | low | reachable | app/admin.py:6 | B404: blacklist |
| bandit:B307:app/admin.py:14 | bandit |  |  | medium | reachable | app/admin.py:14 | B307: blacklist |
| bandit:B301:app/admin.py:19 | bandit |  |  | medium | reachable | app/admin.py:19 | B301: blacklist |
| bandit:B602:app/admin.py:24 | bandit |  |  | high | reachable | app/admin.py:24 | B602: subprocess_popen_with_shell_equals_true |
| pip-audit:PYSEC-2018-28:requests | pip-audit | requests | CVE-2018-18074 | unknown | reachable | app/admin.py:9 | PYSEC-2018-28 in requests |
| pip-audit:PYSEC-2023-74:requests | pip-audit | requests | CVE-2023-32681 | unknown | reachable | app/admin.py:9 | PYSEC-2023-74 in requests |
| pip-audit:PYSEC-2023-74:requests | pip-audit | requests | CVE-2023-32681 | unknown | reachable | app/admin.py:9 | PYSEC-2023-74 in requests |
| pip-audit:PYSEC-2026-1873:requests | pip-audit | requests | CVE-2024-35195 | unknown | reachable | app/admin.py:9 | PYSEC-2026-1873 in requests |
| pip-audit:PYSEC-2026-1872:requests | pip-audit | requests | CVE-2024-47081 | unknown | reachable | app/admin.py:9 | PYSEC-2026-1872 in requests |
| pip-audit:PYSEC-2026-2275:requests | pip-audit | requests | CVE-2026-25645 | unknown | reachable | app/admin.py:9 | PYSEC-2026-2275 in requests |
