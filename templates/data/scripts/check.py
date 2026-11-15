#!/usr/bin/env python3
"""Checks for the private data repo.

Facts, stories, and prices are dated lines with a source. Decisions carry
front matter. Past lines and dated files may not be edited or deleted.
New dated entries are allowed. Run from the data repo, or pass --root.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

FACT_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \| source: ([^|]+?) \| (\S.*)$")
POST_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \| (\S.*)$")
RECORD_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9][a-z0-9-]{1,63})\.md$")
GROWING = ("facts.md", "stories.md", "pricing.md", "voice.md")
RECORD_DIRS = ("me", "customers", "calls", "playbooks", "decisions", "memory", "learnings", "inbox", "inbox/filed")
DECISION_KEYS = ("date", "decision", "why", "supersedes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts/check.py")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--format-only", action="store_true")
    parser.add_argument("--require-example", action="store_true")
    args = parser.parse_args(argv)
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    errors = check(root, format_only=args.format_only, require_example=args.require_example)
    if errors:
        print(f"{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("data check ok")
    return 0


def check(root: Path, format_only: bool = False, require_example: bool = False) -> list[str]:
    errors = check_format(root, require_example)
    if not format_only:
        errors.extend(check_history(root))
    return errors


def check_format(root: Path, require_example: bool) -> list[str]:
    errors: list[str] = []
    for name in ("facts.md", "stories.md", "pricing.md"):
        path = root / name
        if not path.is_file():
            errors.append(f"{name}: missing")
            continue
        errors.extend(_fact_file(name, path.read_text(encoding="utf-8"), require_source=name != "stories.md"))
    voice = root / "voice.md"
    if voice.is_file():
        errors.extend(_voice(voice.read_text(encoding="utf-8")))
    else:
        errors.append("voice.md: missing")
    for relative in _records(root):
        errors.extend(_record(root, relative, require_example))
    return errors


def check_history(root: Path) -> list[str]:
    base = _base_ref(root)
    if base is None:
        return []
    errors: list[str] = []
    for name in GROWING:
        old = _show(root, base, name)
        new_path = root / name
        if old is None:
            continue
        if not new_path.is_file():
            errors.append(f"{name}: deleted; append a new entry instead")
            continue
        if not _is_growing(old, new_path.read_text(encoding="utf-8")):
            errors.append(f"{name}: append-only violation; an existing line was edited or removed")
    for relative in _records(root):
        if relative.startswith("inbox/"):
            continue
        old = _show(root, base, relative)
        if old is None:
            continue
        new = (root / relative).read_text(encoding="utf-8")
        if _norm(old) != _norm(new):
            errors.append(f"{relative}: existing entry was edited")
    old_records = _records_at(root, base)
    for relative in old_records:
        if relative.startswith("inbox/"):
            continue
        if not (root / relative).is_file():
            errors.append(f"{relative}: deleted; add a new dated entry instead")
    return errors


def _fact_file(name: str, text: str, require_source: bool) -> list[str]:
    errors = []
    seen = False
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.startswith("- "):
            continue
        seen = True
        if require_source:
            match = FACT_LINE.match(line)
            if match is None or not match.group(2).strip():
                errors.append(f"{name}:{number}: fact needs a date and a source")
                continue
            if not _date(match.group(1)):
                errors.append(f"{name}:{number}: {match.group(1)} is not a calendar date")
        else:
            match = POST_LINE.match(line)
            if match is None:
                errors.append(f"{name}:{number}: story needs a date")
            elif not _date(match.group(1)):
                errors.append(f"{name}:{number}: {match.group(1)} is not a calendar date")
    if not seen:
        errors.append(f"{name}: needs at least one dated entry")
    return errors


def _voice(text: str) -> list[str]:
    sections = _sections(text)
    errors = []
    for heading in ("Banned words", "Best posts", "Hated posts"):
        if heading.lower() not in sections:
            errors.append(f"voice.md: missing section {heading}")
    banned = sections.get("banned words", "")
    first = next((line for line in banned.splitlines() if line.startswith("- ")), "")
    if not first.lower().startswith("- em dash"):
        errors.append("voice.md: the first banned word must be the em dash")
    for heading in ("best posts", "hated posts"):
        for line in sections.get(heading, "").splitlines():
            if not line.startswith("- "):
                continue
            match = POST_LINE.match(line)
            if match is None or not _date(match.group(1)):
                errors.append(f"voice.md: post entry needs a date: {line}")
    return errors


def _record(root: Path, relative: str, require_example: bool) -> list[str]:
    path = root / relative
    name = Path(relative).name
    if name == "README.md":
        return []
    match = RECORD_NAME.match(name)
    errors = []
    if match is None:
        return [f"{relative}: file name must be YYYY-MM-DD-slug.md"]
    if not _date(match.group(1)):
        errors.append(f"{relative}: {match.group(1)} is not a calendar date")
    try:
        meta, body = _frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return errors + [f"{relative}: {exc}"]
    if meta.get("date") != match.group(1):
        errors.append(f"{relative}: front matter date must match the file name")
    if relative.startswith("decisions/"):
        for key in DECISION_KEYS:
            if key not in meta:
                errors.append(f"{relative}: front matter missing {key}")
    elif "date" not in meta:
        errors.append(f"{relative}: front matter missing date")
    if require_example:
        if meta.get("example") is not True:
            errors.append(f"{relative}: example records set example: true")
        if "EXAMPLE" not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative}: example records contain EXAMPLE")
    if not body.strip() and not relative.startswith("inbox/"):
        errors.append(f"{relative}: body is empty")
    return errors


def _records(root: Path) -> list[str]:
    found = []
    for directory in RECORD_DIRS:
        folder = root / directory
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.md")):
            found.append(path.relative_to(root).as_posix())
    return found


def _records_at(root: Path, base: str) -> list[str]:
    listing = _git(root, ["ls-tree", "-r", "--name-only", base], check=False)
    if listing.returncode != 0:
        return []
    found = []
    for line in listing.stdout.splitlines():
        if not line.endswith(".md"):
            continue
        for directory in RECORD_DIRS:
            if line.startswith(directory + "/") and not line.endswith("/README.md"):
                found.append(line)
    return found


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("front matter is not closed")
    meta: dict[str, object] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"bad front matter line: {line}")
        key, raw = line.split(":", 1)
        meta[key.strip()] = _coerce(raw.strip())
    return meta, text[end + 5 :]


def _sections(text: str) -> dict[str, str]:
    chunks = re.split(r"(?m)^## ", text)
    sections: dict[str, str] = {}
    for chunk in chunks[1:]:
        name, _, rest = chunk.partition("\n")
        sections[name.strip().casefold()] = rest
    return sections


def _coerce(value: str) -> object:
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def _date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n")


def _is_growing(old: str, new: str) -> bool:
    old_lines = [line for line in _norm(old).splitlines() if line.strip()]
    new_lines = [line for line in _norm(new).splitlines() if line.strip()]
    index = 0
    for line in new_lines:
        if index < len(old_lines) and line == old_lines[index]:
            index += 1
    return index == len(old_lines)


def _base_ref(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    import os

    base = os.environ.get("BASE_REF")
    if not base and os.environ.get("GITHUB_BASE_REF"):
        base = "origin/" + os.environ["GITHUB_BASE_REF"]
    if base and _git(root, ["rev-parse", "--verify", base], check=False).returncode == 0:
        head = _git(root, ["rev-parse", "HEAD"]).stdout.strip()
        other = _git(root, ["rev-parse", base]).stdout.strip()
        return None if head == other else base
    for candidate in ("origin/main", "main"):
        if _git(root, ["rev-parse", "--verify", candidate], check=False).returncode != 0:
            continue
        head = _git(root, ["rev-parse", "HEAD"]).stdout.strip()
        other = _git(root, ["rev-parse", candidate]).stdout.strip()
        if head != other:
            return candidate
    return None


def _show(root: Path, base: str, relative: str) -> str | None:
    result = _git(root, ["show", f"{base}:{relative}"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise SystemExit(detail or f"git {' '.join(args)} failed")
    return result


if __name__ == "__main__":
    sys.exit(main())
