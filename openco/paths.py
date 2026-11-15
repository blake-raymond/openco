"""Locations that do not depend on the current working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "data"
POINTER = ROOT / ".openco" / "data-repo"
DEFAULT_DATA_REPO = (ROOT / ".." / "openco-data").resolve()
