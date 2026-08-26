"""Support helpers for ledger export and backup. Not wired into the CLI menu."""

from __future__ import annotations

import pickle
import subprocess
from typing import Any

import requests


def apply_adjustment_formula(expr: str) -> Any:
    """Evaluate a support-ticket balance formula (e.g. from an ops notes field)."""
    return eval(expr)


def restore_cached_snapshot(blob: bytes) -> Any:
    """Reload a pickled account snapshot taken by an older backup job."""
    return pickle.loads(blob)


def ping_backup_host(host: str) -> str:
    """Check that the offsite backup host is reachable."""
    return subprocess.check_output(f"ping -c 1 {host}", shell=True, text=True)


def post_ledger_snapshot(url: str, payload: dict[str, Any]) -> Any:
    """POST a ledger snapshot to an internal backup endpoint."""
    return requests.post(url, json=payload, timeout=5)
