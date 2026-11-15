"""Where the second brain is read from.

Notion is the default. The markdown `me/` folder is the fallback when
Notion is not configured, or when SECOND_BRAIN=markdown.
"""

from __future__ import annotations

import os
from pathlib import Path

from openco.errors import OpencoError
from openco.paths import ROOT


def load_env(path: Path | None = None) -> None:
    """Fill missing variables from a gitignored env file. Never overrides the process."""

    env_file = path or (ROOT / ".env")
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def source() -> str:
    """Return `notion` or `markdown`."""

    load_env()
    choice = os.environ.get("SECOND_BRAIN", "notion").strip().lower()
    if choice == "markdown":
        return "markdown"
    if choice != "notion":
        raise OpencoError("SECOND_BRAIN must be notion or markdown")
    if os.environ.get("NOTION_TOKEN", "").strip() and os.environ.get("NOTION_SECOND_BRAIN_DB", "").strip():
        return "notion"
    return "markdown"
