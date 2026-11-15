"""Where the private data repository is.

Resolution order: an explicit path, OPENCO_DATA_REPO, then the pointer
file written by setup. Relative paths are resolved from the public
repository root, not from the shell's current directory.
"""

import os
from pathlib import Path

from openco.paths import POINTER, ROOT


def configured_data_repo(explicit: str | None = None) -> Path | None:
    raw = explicit or os.environ.get("OPENCO_DATA_REPO")
    if raw:
        return _resolve(raw)
    if POINTER.is_file():
        pointed = POINTER.read_text(encoding="utf-8").strip()
        if pointed:
            return _resolve(pointed)
    return None


def _resolve(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()
