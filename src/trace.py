"""Append-only execution records; never store credentials or private reasoning."""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Trace:
    """A small synchronous JSONL writer safe to share between pipeline stages."""

    _PRIVATE_KEYS = re.compile(
        r"authorization|credential|api[_-]?key|access[_-]?token|secret|password|"
        r"headers|chain[_-]?of[_-]?thought|reasoning|^(messages|prompt|content|source[_-]?text)$",
        re.IGNORECASE,
    )

    def __init__(self, path: Path, secret: str = "") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._secrets = tuple(
            value for value in {secret, os.environ.get("OPENROUTER_API_KEY", "")} if value
        )
        # The output belongs to this run. A fresh trace avoids mixing prior runs.
        self.path.write_text("", encoding="utf-8")

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): (
                    "[REDACTED]"
                    if self._PRIVATE_KEYS.search(str(key))
                    else self._redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._redact(item) for item in value]
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, "[REDACTED]")
            # Also catch accidental bearer credentials when the exact key is unknown.
            return re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", value)
        if isinstance(value, Path):
            return self._redact(str(value))
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return self._redact(str(value))

    def event(self, stage: str, action: str, result: str, **metadata: Any) -> None:
        record = self._redact(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stage": stage,
                "action": action,
                "result": result,
                "metadata": metadata,
            }
        )
        line = json.dumps(record, ensure_ascii=False, allow_nan=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
                handle.flush()
