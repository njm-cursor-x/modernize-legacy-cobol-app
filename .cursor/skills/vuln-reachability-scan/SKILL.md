---
name: vuln-reachability-scan
description: Runs a fixed Bandit (SAST) plus pip-audit (SCA) vulnerability reachability scan on first-party Python under app/ and writes comparable pass-N reports. Use when scanning for vulnerabilities, reachability, pip-audit, Bandit, SCA, or SAST, or when a scan subagent is invoked.
---

# Vulnerability reachability scan

Later scan subagents must run **identical tools and flags** via the bundled runner. Do not invent alternate command lines, scanners, or report shapes.

## Mandatory invocation

Always execute the bundled script. Never run `bandit` or `pip-audit` ad hoc.

```bash
python3 .cursor/skills/vuln-reachability-scan/scripts/scan.py --pass N --root /workspace
```

- `--pass N` is required (integer, including `0`). Use the pass number from the parent orchestrator.
- `--root` defaults to the repo root (detected from cwd / `.git` / `/workspace`). Pass it explicitly when the orchestrator already knows the root.

The script writes **both**:

- `reports/security/pass-N.md`
- `reports/security/pass-N.json`

It creates `reports/security/` if missing. JSON schema and an example live in [reference.md](reference.md).

Exit code: the script exits **0 when findings exist**. Non-zero means the runner or a scanner failed (missing binary, crash, network error talking to the advisory service). The orchestrator owns the gate.

## What the runner does (do not reimplement)

1. **Bandit (SAST)** on first-party Python under `{root}/app/` (`-r`, JSON, quiet). First-party Bandit issues are marked `reachability: reachable` (it is our code). Severity: `HIGH` → `high`, `MEDIUM` → `medium`, `LOW` → `low`.
2. **pip-audit (SCA)** against a lockfile/requirements file if present. JSON output. Advisories are classified with a **module-level import graph** of `app/*.py` (stdlib `ast` only):
   - `reachable`: a mapped import name of the vulnerable distribution appears in the app import graph
   - `unreachable`: mapped, but not imported by app code
   - `unknown`: cannot map the distribution name to import module name(s)
3. Records scanner **versions** and **exact command lines** in the JSON `scanners` array.

Lockfile lookup (first match wins): `{root}/uv.lock`, `{root}/requirements.txt`, `{root}/app/uv.lock`, `{root}/app/requirements.txt`. Prefer `uv.lock` over `requirements.txt` when both exist at the same level. If `uv.lock` is used, the script materializes pinned `name==version` lines and points pip-audit at that file. If no lockfile exists, pip-audit is skipped (recorded in `scanners` / notes), not run against the ambient environment.

Fixed pip-audit flags (do not change): `-r <file> -f json --progress-spinner off --no-deps --disable-pip -o <tmp>`. `--no-deps --disable-pip` audits the pin file as written (no venv/resolver). Pins must be `name==version` (or comments-only). Fixed Bandit flags: `-r <app> -x .venv,venv,__pycache__ -f json -q -o <tmp>`.

If `{root}/app/` is missing, the script skips Bandit and the import graph, writes a valid empty-findings report plus a note, and exits 0. pip-audit still runs when a lockfile exists.

## Reachability limits (do not overclaim)

This is **module-level** reachability from static imports. It is **not** function-level, call-graph, or commercial reachability (no Endor Labs / Socket / GitHub reachability, no “this CVE is exploitable on this path”). Do not upgrade `reachable` to “exploitable” or invent per-function evidence.

Bandit evidence is the issue text and `file:line`. pip-audit evidence is the import site (`file:line`) when reachable, otherwise the advisory id / package.

## Severity (pip-audit)

If the advisory JSON includes a CVSS score: `>= 9.0` critical, `>= 7.0` high, `>= 4.0` medium, else low. If a vendor severity string is present (`critical|high|medium|low`), use that. Otherwise **`unknown`** (do not silently promote to `high`; the orchestrator may treat `unknown` as high if it wants a conservative gate).

## Agent checklist

1. Read this skill and [reference.md](reference.md).
2. Install Bandit and pip-audit if missing: `pip install bandit pip-audit`.
3. Run **only** the bundled script with `--pass` and `--root`.
4. Do not plant vulnerabilities, do not move COBOL sources, do not change app behavior.
5. Return the two report paths, finding counts by severity, and the script exit code. Do not reformat the JSON schema.
