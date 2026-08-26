# Report schema (pass-N.json)

Both `reports/security/pass-N.json` and `reports/security/pass-N.md` are required. Extra optional keys (`notes`) are allowed; required keys below must be present and typed as shown.

## JSON schema

```json
{
  "pass": 1,
  "generated_at": "ISO-8601",
  "scanners": [
    {"name": "bandit", "version": "...", "command": "..."},
    {"name": "pip-audit", "version": "...", "command": "..."}
  ],
  "findings": [
    {
      "id": "stable-id",
      "source": "bandit|pip-audit",
      "package": null,
      "cve": null,
      "severity": "critical|high|medium|low|unknown",
      "reachability": "reachable|unreachable|unknown|n/a",
      "evidence": "import or call site or bandit issue text",
      "location": "file:line",
      "title": "short title"
    }
  ]
}
```

### Field rules

| Field | Rules |
| --- | --- |
| `pass` | Integer from `--pass`. |
| `generated_at` | UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`). |
| `scanners[].name` | `bandit` or `pip-audit`. |
| `scanners[].version` | Tool `--version` output (trimmed). |
| `scanners[].command` | Exact argv joined as a string, or a skip reason if the tool did not run. |
| `findings[].id` | Stable. Bandit: `bandit:{test_id}:{relpath}:{line}`. pip-audit: `pip-audit:{advisory-id}:{package}`. |
| `findings[].source` | `bandit` or `pip-audit`. |
| `findings[].package` | Distribution name for pip-audit; `null` for Bandit. |
| `findings[].cve` | First `CVE-…` alias if present; otherwise `null`. |
| `findings[].severity` | One of `critical`, `high`, `medium`, `low`, `unknown`. |
| `findings[].reachability` | Bandit first-party: `reachable`. pip-audit: `reachable` / `unreachable` / `unknown`. Use `n/a` only if a finding cannot be classified (should be rare). |
| `findings[].evidence` | Bandit `issue_text`, or import-site / advisory summary for pip-audit. |
| `findings[].location` | `path/relative/to/root:line`. pip-audit unreachable/unknown may use the lockfile path with line `0`. |
| `findings[].title` | Short human title (`B201: flask_debug_true`, advisory id, etc.). |
| `notes` | Optional string array (missing `app/`, skipped pip-audit, etc.). |

Reachability is **module-level static imports only**. Reports must not claim function-level or commercial reachability.

## Markdown report

`pass-N.md` must include:

1. Pass number and `generated_at`
2. Optional notes
3. Counts by severity (and by reachability)
4. A findings table: id, source, package, CVE, severity, reachability, location, title

Empty findings: still write both files, with zero counts and an empty table (or an explicit “No findings” row).

## Example

```json
{
  "pass": 1,
  "generated_at": "2026-08-26T13:00:00Z",
  "scanners": [
    {
      "name": "bandit",
      "version": "1.9.4",
      "command": "bandit -r /workspace/app -x .venv,venv,__pycache__ -f json -q -o /tmp/bandit.json"
    },
    {
      "name": "pip-audit",
      "version": "2.10.1",
      "command": "pip-audit -r /workspace/requirements.txt -f json --progress-spinner off --no-deps --disable-pip -o /tmp/pip-audit.json"
    }
  ],
  "notes": [],
  "findings": [
    {
      "id": "bandit:B201:app/main.py:42",
      "source": "bandit",
      "package": null,
      "cve": null,
      "severity": "medium",
      "reachability": "reachable",
      "evidence": "A Flask app appears to be run with debug=True, which exposes a Werkzeug debugger.",
      "location": "app/main.py:42",
      "title": "B201: flask_debug_true"
    },
    {
      "id": "pip-audit:GHSA-xxxx-yyyy-zzzz:requests",
      "source": "pip-audit",
      "package": "requests",
      "cve": "CVE-2024-0000",
      "severity": "unknown",
      "reachability": "reachable",
      "evidence": "import requests (app/main.py:3)",
      "location": "app/main.py:3",
      "title": "GHSA-xxxx-yyyy-zzzz in requests"
    }
  ]
}
```
