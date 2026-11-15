"""Where your data repo is.

Resolution order: an explicit path, OPENCO_DATA_REPO, the pointer file
written by setup, then the path stored in the setup state. Relative
paths are resolved from this checkout. There is no built-in name.
"""

import json
import os
from pathlib import Path

from openco.paths import POINTER, ROOT, STATE


def configured_data_repo(explicit: str | None = None) -> Path | None:
    raw = explicit or os.environ.get("OPENCO_DATA_REPO")
    if raw:
        return _resolve(raw)
    if POINTER.is_file():
        pointed = POINTER.read_text(encoding="utf-8").strip()
        if pointed:
            return _resolve(pointed)
    if STATE.is_file():
        try:
            record = json.loads(STATE.read_text(encoding="utf-8")).get("data_repo") or {}
        except json.JSONDecodeError:
            record = {}
        path = record.get("path") if isinstance(record, dict) else None
        if path:
            return _resolve(str(path))
    return None


def _resolve(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()
