"""Shape of the markdown brain.

Logs are append-only files of dated entries. Record files are one note
each, named with the date, and are not edited after they are committed.
"""

import re
from datetime import datetime
from pathlib import Path

HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) - ([a-z][a-z0-9-]{2,63})$")
RECORD_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z][a-z0-9-]{2,63})\.md$")

LOGS = (
    "facts/FACTS.md",
    "stories/STORIES.md",
    "company-brain/decisions/DECISIONS.md",
    "voice/best.md",
    "voice/hate.md",
    "voice/never-use.md",
)

RECORD_DIRS = (
    "second-brain",
    "transcripts",
    "company-brain/customers",
    "company-brain/numbers",
    "company-brain/pricing",
    "company-brain/playbooks",
    "inbox/examples",
)

KEYED_RECORD_DIRS = ("transcripts", "inbox/examples")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def is_append(old: str, new: str) -> bool:
    previous = normalize(old)
    current = normalize(new)
    if not previous.endswith("\n"):
        previous += "\n"
    return current.startswith(previous)


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("frontmatter is not closed")
    meta: dict[str, object] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"bad frontmatter line: {line}")
        key, raw = line.split(":", 1)
        meta[key.strip()] = _coerce(raw.strip())
    return meta, text[end + 5 :]


def check_log(path: str, text: str, require_example: bool) -> list[str]:
    errors: list[str] = []
    lines = normalize(text).splitlines()
    if not lines or not lines[0].startswith("# "):
        errors.append(f"{path}: must start with a level-1 heading")
    indexes = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not indexes:
        errors.append(f"{path}: needs at least one dated entry")
        return errors
    seen: list[str] = []
    for number, start in enumerate(indexes):
        match = HEADING.match(lines[start])
        if match is None:
            errors.append(f"{path}:{start + 1}: heading must be '## YYYY-MM-DD - slug'")
            continue
        date, slug = match.group(1), match.group(2)
        if not valid_date(date):
            errors.append(f"{path}:{start + 1}: {date} is not a calendar date")
        if slug in seen:
            errors.append(f"{path}: duplicate slug {slug}")
        seen.append(slug)
        end = indexes[number + 1] if number + 1 < len(indexes) else len(lines)
        body = "\n".join(lines[start + 1 : end]).strip()
        if not body:
            errors.append(f"{path}:{start + 1}: entry is empty")
        elif require_example and "EXAMPLE" not in body:
            errors.append(f"{path}:{start + 1}: example entry must contain EXAMPLE")
    return errors


def check_record(path: str, text: str, require_example: bool) -> list[str]:
    errors: list[str] = []
    name = Path(path).name
    match = RECORD_NAME.match(name)
    if match is None:
        errors.append(f"{path}: record file name must be YYYY-MM-DD-slug.md")
        return errors
    file_date, file_slug = match.group(1), match.group(2)
    if not valid_date(file_date):
        errors.append(f"{path}: {file_date} is not a calendar date")
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        return errors + [f"{path}: {exc}"]
    if meta.get("date") != file_date:
        errors.append(f"{path}: frontmatter date must match the file name")
    parent = str(Path(path).parent).replace("\\", "/")
    if parent in KEYED_RECORD_DIRS and meta.get("key") != file_slug:
        errors.append(f"{path}: frontmatter key must match the file name slug")
    if parent in KEYED_RECORD_DIRS and meta.get("kind") not in {"voice-note", "meeting"}:
        errors.append(f"{path}: kind must be voice-note or meeting")
    if not body.strip():
        errors.append(f"{path}: body is empty")
    if require_example:
        if meta.get("example") is not True:
            errors.append(f"{path}: example records set example: true")
        if "EXAMPLE" not in body:
            errors.append(f"{path}: example records contain EXAMPLE in the body")
    return errors


def slug_in_log(text: str, slug: str) -> bool:
    for line in normalize(text).splitlines():
        match = HEADING.match(line)
        if match and match.group(2) == slug:
            return True
    return False


def _coerce(value: str) -> object:
    if value == "true":
        return True
    if value == "false":
        return False
    return value
