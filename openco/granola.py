"""Turn a transcript into a dated call file.

Granola's documented export is a CSV from Settings > Profile. The public
docs do not name the CSV columns, so this module does not parse that
file. It reads the generic transcript documented in docs/setup/granola.md.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

from openco.config import configured_data_repo
from openco.errors import OpencoError

_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    source = None
    data_arg = None
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--data-repo":
            index += 1
            if index >= len(args):
                raise OpencoError("--data-repo needs a path")
            data_arg = args[index]
        elif item.startswith("-"):
            raise OpencoError(f"unknown argument {item}")
        elif source is None:
            source = item
        else:
            raise OpencoError("usage: scripts/import-granola FILE")
        index += 1
    if source is None:
        raise OpencoError("usage: scripts/import-granola FILE")
    data_repo = configured_data_repo(data_arg)
    if data_repo is None or not data_repo.is_dir():
        raise OpencoError("no private data repo. Run make setup or pass --data-repo.")
    relative = write_call(data_repo, Path(source).read_text(encoding="utf-8"))
    print(f"wrote {relative}")
    print("Commit that file on a branch. Do not commit it to main.")
    return 0


def write_call(data_repo: Path, text: str) -> str:
    relative, markdown = convert(text)
    path = data_repo / relative
    if path.exists():
        raise OpencoError(f"{relative} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return relative


def convert(text: str) -> tuple[str, str]:
    if _looks_like_csv(text):
        raise OpencoError(
            "This looks like CSV. Granola's documented export is a CSV from "
            "Settings > Profile > Generate CSV. The public docs say that file "
            "includes the title, summary, transcript, and other details, but "
            "they do not name the columns, so this script does not parse it. "
            "Save the meeting as the generic transcript in docs/setup/granola.md."
        )
    meta, body = _frontmatter(text)
    date = str(meta.get("date", ""))
    title = str(meta.get("title", "")).strip()
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise OpencoError("generic transcript needs a front matter date: YYYY-MM-DD") from exc
    if not title:
        raise OpencoError("generic transcript needs a front matter title")
    slug = _slug(title)
    example = meta.get("example") is True
    header = ["---", f"date: {date}", f"title: {title}", "source: generic-transcript"]
    if example:
        header.append("example: true")
    header.extend(["---", "", f"# {title}", ""])
    prose = body.strip()
    if not prose:
        raise OpencoError("generic transcript needs a body")
    markdown = "\n".join(header) + prose + "\n"
    return f"calls/{date}-{slug}.md", markdown


def _looks_like_csv(text: str) -> bool:
    stripped = text.lstrip()
    if stripped.startswith("---") or stripped.startswith("#") or stripped.startswith("{"):
        return False
    first = stripped.splitlines()[0] if stripped else ""
    return "," in first


def _slug(title: str) -> str:
    slug = _SLUG_CHARS.sub("-", title.casefold()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise OpencoError("title did not produce a file name")
    return slug[:64].strip("-")


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise OpencoError(
            "transcript needs front matter with date and title. "
            "See docs/setup/granola.md for the generic format."
        )
    end = text.find("\n---\n", 4)
    if end < 0:
        raise OpencoError("front matter is not closed")
    meta: dict[str, object] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value: object = raw.strip()
        if value == "true":
            value = True
        meta[key.strip()] = value
    return meta, text[end + 5 :]
