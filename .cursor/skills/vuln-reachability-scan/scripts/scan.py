#!/usr/bin/env python3
"""Fixed Bandit + pip-audit vulnerability reachability scan runner.

Scan subagents must invoke this script rather than ad-hoc scanner CLIs.
Exits 0 when findings exist; non-zero only on tool/script failure.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


SKIP_DIR_NAMES = {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox"}
BANDIT_EXCLUDE = ".venv,venv,__pycache__"
CVE_RE = re.compile(r"^CVE-\d{4}-\d+", re.IGNORECASE)

# Dist name -> import names when metadata is unavailable.
KNOWN_IMPORT_NAMES: dict[str, list[str]] = {
    "pyyaml": ["yaml"],
    "pillow": ["PIL"],
    "beautifulsoup4": ["bs4"],
    "python-dateutil": ["dateutil"],
    "protobuf": ["google"],
    "opencv-python": ["cv2"],
    "scikit-learn": ["sklearn"],
    "attrs": ["attr", "attrs"],
    "pyjwt": ["jwt"],
    "pycryptodome": ["Crypto"],
    "pycrypto": ["Crypto"],
    "typing-extensions": ["typing_extensions"],
    "importlib-metadata": ["importlib_metadata"],
    "importlib-resources": ["importlib_resources"],
    "python-dotenv": ["dotenv"],
    "psycopg2-binary": ["psycopg2"],
    "pyopenssl": ["OpenSSL"],
    "pytz": ["pytz"],
    "jinja2": ["jinja2"],
    "markdown": ["markdown"],
}


class ScanError(Exception):
    """Unrecoverable runner/tool failure (should exit non-zero)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".git").exists() or (candidate / "main.cob").exists():
            return candidate
    workspace = Path("/workspace")
    if workspace.is_dir():
        return workspace
    return cwd


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    home_bin = Path.home() / ".local" / "bin" / name
    if home_bin.is_file() and os.access(home_bin, os.X_OK):
        return str(home_bin)
    raise ScanError(
        f"{name} not found on PATH or {home_bin}. Install with: pip install bandit pip-audit"
    )


def tool_version(binary: str) -> str:
    proc = subprocess.run(
        [binary, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    text = (proc.stdout or proc.stderr or "").strip()
    first = text.splitlines()[0].strip() if text else ""
    return first or "unknown"


def join_cmd(argv: list[str]) -> str:
    return shlex.join(argv)


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def find_lockfile(root: Path) -> tuple[str, Path] | None:
    for kind, path in (
        ("uv.lock", root / "uv.lock"),
        ("requirements.txt", root / "requirements.txt"),
        ("uv.lock", root / "app" / "uv.lock"),
        ("requirements.txt", root / "app" / "requirements.txt"),
    ):
        if path.is_file():
            return kind, path
    return None


def uv_lock_to_requirements(lock_path: Path) -> str:
    if tomllib is None:
        raise ScanError("tomllib is required to parse uv.lock (Python 3.11+)")
    raw = lock_path.read_bytes()
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ScanError(f"failed to parse {lock_path}: {exc}") from exc
    lines: list[str] = []
    for pkg in data.get("package") or []:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        version = pkg.get("version")
        source = pkg.get("source") or {}
        if not name or not version:
            continue
        if isinstance(source, dict) and (
            "virtual" in source or "editable" in source or "directory" in source
        ):
            continue
        lines.append(f"{name}=={version}")
    return "\n".join(lines) + ("\n" if lines else "")


def iter_py_files(base: Path) -> list[Path]:
    files: list[Path] = []
    if not base.is_dir():
        return files
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            if name.endswith(".py"):
                files.append(Path(dirpath) / name)
    return sorted(files)


def collect_import_graph(app_dir: Path, root: Path) -> dict[str, list[tuple[str, int]]]:
    """Map top-level imported module name -> [(relpath, lineno), ...]."""
    graph: dict[str, list[tuple[str, int]]] = {}
    for py_file in iter_py_files(app_dir):
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        loc = relpath(py_file, root)
        for node in ast.walk(tree):
            names: list[str] = []
            lineno = getattr(node, "lineno", 1)
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names if alias.name]
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    names = [node.module.split(".")[0]]
            for top in names:
                if not top:
                    continue
                graph.setdefault(top, []).append((loc, lineno))
    return graph


def dist_import_names(dist_name: str) -> tuple[list[str], bool]:
    """Return (import names, confident mapping?)."""
    canonical = dist_name.replace("_", "-").lower()
    names: list[str] = []
    confident = False

    try:
        from importlib.metadata import distribution

        dist = distribution(dist_name)
        top = dist.read_text("top_level.txt")
        if top:
            names = [line.strip() for line in top.splitlines() if line.strip()]
            if names:
                return names, True
    except Exception:
        pass

    if canonical in KNOWN_IMPORT_NAMES:
        return list(KNOWN_IMPORT_NAMES[canonical]), True

    heuristic = dist_name.replace("-", "_")
    names = [heuristic]
    confident = "-" not in dist_name and "." not in dist_name
    return names, confident


def classify_pip_audit(
    dist_name: str, graph: dict[str, list[tuple[str, int]]]
) -> tuple[str, str, str]:
    """Return (reachability, evidence, location)."""
    import_names, confident = dist_import_names(dist_name)
    sites: list[tuple[str, int]] = []
    matched: str | None = None
    for name in import_names:
        if name in graph:
            sites = graph[name]
            matched = name
            break
    if sites and matched:
        rel, line = sites[0]
        return (
            "reachable",
            f"import {matched} ({rel}:{line})",
            f"{rel}:{line}",
        )
    if confident:
        mapped = ", ".join(import_names) or dist_name
        return (
            "unreachable",
            f"{dist_name} maps to [{mapped}] which is not imported by app/",
            "n/a:0",
        )
    return (
        "unknown",
        f"cannot map distribution {dist_name!r} to an import name",
        "n/a:0",
    )


def map_bandit_severity(raw: str) -> str:
    return {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(
        (raw or "").upper(), "unknown"
    )


def map_cvss_severity(payload: dict[str, Any]) -> str:
    for key in ("severity", "Severity"):
        val = payload.get(key)
        if isinstance(val, str) and val.lower() in {
            "critical",
            "high",
            "medium",
            "low",
            "unknown",
        }:
            return val.lower()
    score: float | None = None
    for key in ("cvss_score", "cvss", "CVSS"):
        val = payload.get(key)
        if isinstance(val, (int, float)):
            score = float(val)
            break
        if isinstance(val, dict):
            for inner in ("score", "baseScore", "base_score"):
                if isinstance(val.get(inner), (int, float)):
                    score = float(val[inner])
                    break
        if score is not None:
            break
    if score is None:
        return "unknown"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


def first_cve(vuln_id: str, aliases: list[str]) -> str | None:
    for item in [vuln_id, *aliases]:
        if not item:
            continue
        match = CVE_RE.match(item)
        if match:
            return match.group(0).upper()
    return None


def run_json_tool(
    argv: list[str],
    output_path: Path,
    allowed_codes: set[int],
) -> None:
    proc = subprocess.run(argv, check=False, capture_output=True, text=True)
    if proc.returncode not in allowed_codes:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise ScanError(
            f"{argv[0]} failed (exit {proc.returncode}): {detail[-4000:]}"
        )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        stdout = (proc.stdout or "").strip()
        if stdout.startswith(("{", "[")):
            output_path.write_text(proc.stdout, encoding="utf-8")
        else:
            err = (proc.stderr or "").strip()
            raise ScanError(
                f"{argv[0]} produced no JSON output at {output_path}"
                + (f": {err[-2000:]}" if err else "")
            )


def parse_bandit_findings(payload: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for issue in payload.get("results") or []:
        filename = Path(issue.get("filename") or "")
        rel = relpath(filename, root) if filename.parts else "unknown"
        line = int(issue.get("line_number") or 1)
        test_id = str(issue.get("test_id") or "B000")
        test_name = str(issue.get("test_name") or test_id)
        text = str(issue.get("issue_text") or "").strip()
        findings.append(
            {
                "id": f"bandit:{test_id}:{rel}:{line}",
                "source": "bandit",
                "package": None,
                "cve": None,
                "severity": map_bandit_severity(str(issue.get("issue_severity") or "")),
                "reachability": "reachable",
                "evidence": text,
                "location": f"{rel}:{line}",
                "title": f"{test_id}: {test_name}",
            }
        )
    return findings


def parse_pip_audit_findings(
    payload: Any,
    graph: dict[str, list[tuple[str, int]]],
    lock_rel: str,
) -> list[dict[str, Any]]:
    deps: list[dict[str, Any]]
    if isinstance(payload, dict):
        deps = list(payload.get("dependencies") or [])
    elif isinstance(payload, list):
        deps = payload
    else:
        deps = []
    findings: list[dict[str, Any]] = []
    for dep in deps:
        if not isinstance(dep, dict):
            continue
        if dep.get("skip_reason"):
            continue
        name = str(dep.get("name") or "")
        if not name:
            continue
        for vuln in dep.get("vulns") or []:
            if not isinstance(vuln, dict):
                continue
            vuln_id = str(vuln.get("id") or "UNKNOWN")
            aliases = [str(a) for a in (vuln.get("aliases") or [])]
            cve = first_cve(vuln_id, aliases)
            reachability, evidence, location = classify_pip_audit(name, graph)
            if location.startswith("n/a"):
                location = f"{lock_rel}:0"
            desc = str(vuln.get("description") or "").strip()
            if desc and reachability != "reachable":
                evidence = f"{evidence}. {desc[:240]}"
            elif reachability == "reachable" and desc:
                evidence = f"{evidence}. {desc[:240]}"
            findings.append(
                {
                    "id": f"pip-audit:{vuln_id}:{name}",
                    "source": "pip-audit",
                    "package": name,
                    "cve": cve,
                    "severity": map_cvss_severity(vuln),
                    "reachability": reachability,
                    "evidence": evidence,
                    "location": location,
                    "title": f"{vuln_id} in {name}",
                }
            )
    return findings


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    findings: list[dict[str, Any]] = report.get("findings") or []
    sev_counts = Counter(f.get("severity") or "unknown" for f in findings)
    reach_counts = Counter(f.get("reachability") or "n/a" for f in findings)
    order = ["critical", "high", "medium", "low", "unknown"]
    reach_order = ["reachable", "unreachable", "unknown", "n/a"]

    lines = [
        f"# Vulnerability reachability scan — pass {report['pass']}",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "Reachability is **module-level** (static imports in `app/`). "
        "This is not function-level or commercial reachability.",
        "",
        "## Scanners",
        "",
        "| Name | Version | Command |",
        "| --- | --- | --- |",
    ]
    for sc in report.get("scanners") or []:
        cmd = str(sc.get("command") or "").replace("|", "\\|")
        lines.append(f"| {sc.get('name')} | {sc.get('version')} | `{cmd}` |")
    notes = report.get("notes") or []
    if notes:
        lines.extend(["", "## Notes", ""])
        for note in notes:
            lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Summary by severity",
            "",
            "| Severity | Count |",
            "| --- | ---: |",
        ]
    )
    for sev in order:
        lines.append(f"| {sev} | {sev_counts.get(sev, 0)} |")
    lines.append(f"| **total** | **{len(findings)}** |")
    lines.extend(
        [
            "",
            "## Summary by reachability",
            "",
            "| Reachability | Count |",
            "| --- | ---: |",
        ]
    )
    for key in reach_order:
        lines.append(f"| {key} | {reach_counts.get(key, 0)} |")
    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )
    if not findings:
        lines.append("No findings.")
    else:
        lines.extend(
            [
                "| ID | Source | Package | CVE | Severity | Reachability | Location | Title |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for f in findings:

            def cell(value: Any) -> str:
                text = "" if value is None else str(value)
                return text.replace("|", "\\|").replace("\n", " ")

            lines.append(
                "| "
                + " | ".join(
                    [
                        cell(f.get("id")),
                        cell(f.get("source")),
                        cell(f.get("package")),
                        cell(f.get("cve")),
                        cell(f.get("severity")),
                        cell(f.get("reachability")),
                        cell(f.get("location")),
                        cell(f.get("title")),
                    ]
                )
                + " |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def scan(pass_n: int, root: Path) -> dict[str, Any]:
    root = root.resolve()
    reports_dir = root / "reports" / "security"
    reports_dir.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []
    findings: list[dict[str, Any]] = []
    scanners: list[dict[str, str]] = []

    bandit_bin = find_tool("bandit")
    pip_audit_bin = find_tool("pip-audit")
    bandit_ver = tool_version(bandit_bin)
    pip_ver = tool_version(pip_audit_bin)

    app_dir = root / "app"
    graph: dict[str, list[tuple[str, int]]] = {}

    with tempfile.TemporaryDirectory(prefix="vuln-reach-") as tmp:
        tmpdir = Path(tmp)
        bandit_json = tmpdir / "bandit.json"
        pip_json = tmpdir / "pip-audit.json"

        if not app_dir.is_dir():
            notes.append("app/ not present; skipped Bandit and import-graph scan")
            scanners.append(
                {
                    "name": "bandit",
                    "version": bandit_ver,
                    "command": f"skipped (no {relpath(app_dir, root)} directory)",
                }
            )
        else:
            graph = collect_import_graph(app_dir, root)
            bandit_cmd = [
                bandit_bin,
                "-r",
                str(app_dir),
                "-x",
                BANDIT_EXCLUDE,
                "-f",
                "json",
                "-q",
                "-o",
                str(bandit_json),
            ]
            scanners.append(
                {
                    "name": "bandit",
                    "version": bandit_ver,
                    "command": join_cmd(bandit_cmd),
                }
            )
            run_json_tool(bandit_cmd, bandit_json, allowed_codes={0, 1})
            try:
                bandit_payload = json.loads(bandit_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ScanError(f"bandit JSON was not parseable: {exc}") from exc
            findings.extend(parse_bandit_findings(bandit_payload, root))

        lock = find_lockfile(root)
        if lock is None:
            notes.append(
                "no requirements.txt or uv.lock at repo root or app/; skipped pip-audit"
            )
            scanners.append(
                {
                    "name": "pip-audit",
                    "version": pip_ver,
                    "command": "skipped (no requirements.txt or uv.lock)",
                }
            )
        else:
            kind, lock_path = lock
            req_path = lock_path
            extra_note = None
            if kind == "uv.lock":
                exported = tmpdir / "uv-export-requirements.txt"
                exported.write_text(uv_lock_to_requirements(lock_path), encoding="utf-8")
                req_path = exported
                extra_note = f"pip-audit input materialized from {relpath(lock_path, root)}"
            # --no-deps --disable-pip: audit the pin file as written, no venv/resolver.
            pip_cmd = [
                pip_audit_bin,
                "-r",
                str(req_path),
                "-f",
                "json",
                "--progress-spinner",
                "off",
                "--no-deps",
                "--disable-pip",
                "-o",
                str(pip_json),
            ]
            command = join_cmd(pip_cmd)
            if extra_note:
                command = f"{command}  # {extra_note}"
                notes.append(extra_note)
            scanners.append(
                {
                    "name": "pip-audit",
                    "version": pip_ver,
                    "command": command,
                }
            )
            run_json_tool(pip_cmd, pip_json, allowed_codes={0, 1})
            try:
                pip_payload = json.loads(pip_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ScanError(f"pip-audit JSON was not parseable: {exc}") from exc
            findings.extend(
                parse_pip_audit_findings(pip_payload, graph, relpath(lock_path, root))
            )

    report = {
        "pass": pass_n,
        "generated_at": utc_now(),
        "scanners": scanners,
        "notes": notes,
        "findings": findings,
    }
    json_path = reports_dir / f"pass-{pass_n}.json"
    md_path = reports_dir / f"pass-{pass_n}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(md_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Bandit + pip-audit with module-level reachability and write pass-N reports."
    )
    parser.add_argument("--pass", dest="pass_n", type=int, required=True, help="Scan pass number")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: detect from cwd / /workspace)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve() if args.root else detect_root()
    try:
        report = scan(args.pass_n, root)
    except ScanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    n = len(report.get("findings") or [])
    print(
        f"wrote reports/security/pass-{args.pass_n}.json and "
        f"reports/security/pass-{args.pass_n}.md ({n} finding(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
