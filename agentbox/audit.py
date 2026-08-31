"""Append-only, hash-chained JSONL audit log.

Each record embeds the hash of the previous record; verify() recomputes the
chain so any edit, deletion, or reorder of past records is detectable.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


class AuditError(ValueError):
    """Raised when an audit log fails verification."""


def _record_hash(prev: str, body: dict) -> str:
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev + canon).encode()).hexdigest()


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._prev = GENESIS
        if self.path.exists():
            lines = self.path.read_text().splitlines()
            if lines:
                self._prev = json.loads(lines[-1])["hash"]

    def append(self, event: str, **data: object) -> dict:
        body = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "event": event,
            "data": data,
            "prev": self._prev,
        }
        record = {**body, "hash": _record_hash(self._prev, body)}
        with self.path.open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        self._prev = record["hash"]
        return record


def verify(path: str | Path) -> int:
    """Return the number of valid records; raise AuditError on tampering."""
    prev = GENESIS
    count = 0
    for lineno, line in enumerate(Path(path).read_text().splitlines(), start=1):
        record = json.loads(line)
        body = {k: v for k, v in record.items() if k != "hash"}
        if record.get("prev") != prev:
            raise AuditError(f"line {lineno}: broken chain (prev mismatch)")
        if record.get("hash") != _record_hash(prev, body):
            raise AuditError(f"line {lineno}: record hash mismatch (tampered?)")
        prev = record["hash"]
        count += 1
    return count
