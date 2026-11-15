"""File a voice note or meeting transcript into the private brain.

The raw note is copied to transcripts/. Facts, stories, and decisions
are appended to their logs. Existing entries are left untouched.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from openco.errors import OpencoError
from openco.format import parse_frontmatter, slug_in_log, valid_date
from openco.gitutil import commit

_ENTRY_FIELDS = {"title", "category", "because"}
_FIELD_LINE = re.compile(r"^([a-z_]+): (.*)$")
_SLUG = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_FACT_CATEGORIES = {"claim", "story", "number", "pricing"}


def ingest_file(data_repo: Path, source: Path) -> list[str]:
    text = source.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        raise OpencoError(f"{source.name}: {exc}") from exc
    date = meta.get("date")
    key = meta.get("key")
    kind = meta.get("kind")
    if not isinstance(date, str) or not valid_date(date):
        raise OpencoError(f"{source.name}: frontmatter date must be YYYY-MM-DD")
    if not isinstance(key, str) or _SLUG.match(key) is None:
        raise OpencoError(f"{source.name}: frontmatter key must be a lowercase slug")
    if kind not in {"voice-note", "meeting"}:
        raise OpencoError(f"{source.name}: kind must be voice-note or meeting")
    _, sections = _sections(body)
    planned = _plan(sections)
    for log_rel, slug, _entry in planned:
        log_path = data_repo / log_rel
        if not log_path.is_file():
            raise OpencoError(f"missing log {log_rel} in {data_repo}")
        if slug_in_log(log_path.read_text(encoding="utf-8"), slug):
            raise OpencoError(f"{slug} is already in {log_rel}")
    transcript_rel = f"transcripts/{date}-{key}.md"
    transcript_path = data_repo / transcript_rel
    if transcript_path.exists():
        raise OpencoError(f"{transcript_rel} already exists")
    transcript_path.write_text(text, encoding="utf-8")
    written = [transcript_rel]
    filed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for log_rel, slug, block_body in planned:
        block = _block(date, slug, block_body, transcript_rel, filed)
        _append(data_repo / log_rel, block)
        if log_rel not in written:
            written.append(log_rel)
    commit(data_repo, f"File {key} into the brain", written)
    return written


def resolve_source(data_repo: Path, raw: str) -> Path:
    direct = Path(raw)
    if direct.is_file():
        return direct
    inside = data_repo / raw
    if inside.is_file():
        return inside
    raise OpencoError(f"no such note: {raw}")


def _plan(sections: dict[str, str]) -> list[tuple[str, str, str]]:
    planned: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    mapping = (
        ("facts", "facts/FACTS.md", None),
        ("stories", "stories/STORIES.md", "story"),
        ("decisions", "company-brain/decisions/DECISIONS.md", "decision"),
    )
    for section_name, log_rel, forced in mapping:
        for slug, fields, entry_body in _entries(sections.get(section_name, "")):
            if slug in seen:
                raise OpencoError(f"duplicate slug in the note: {slug}")
            seen.add(slug)
            if forced == "story":
                fields["category"] = "story"
            if forced == "decision" and "because" not in fields:
                raise OpencoError(f"decision {slug} needs a because line")
            if log_rel == "facts/FACTS.md":
                category = fields.get("category", "claim")
                if category not in _FACT_CATEGORIES:
                    raise OpencoError(f"fact {slug} category must be claim, story, number, or pricing")
                fields["category"] = category
            planned.append((log_rel, slug, _entry_body(fields, entry_body)))
    return planned


def _entry_body(fields: dict[str, str], body: str) -> str:
    lines = []
    if "title" in fields:
        lines.append(f"title: {fields['title']}")
    if "category" in fields:
        lines.append(f"category: {fields['category']}")
    if "because" in fields:
        lines.append(f"because: {fields['because']}")
    if lines:
        lines.append("")
    lines.append(body.strip())
    return "\n".join(lines).strip()


def _block(date: str, slug: str, body: str, source: str, filed: str) -> str:
    return f"\n## {date} - {slug}\n\n{body}\n\nsource: {source}\nfiled: {filed}\n"


def _append(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + block, encoding="utf-8")


def _sections(body: str) -> tuple[str, dict[str, str]]:
    chunks = re.split(r"(?m)^## ", body)
    sections: dict[str, str] = {}
    for chunk in chunks[1:]:
        name, _, rest = chunk.partition("\n")
        sections[name.strip().casefold()] = rest
    return chunks[0], sections


def _entries(section: str) -> list[tuple[str, dict[str, str], str]]:
    items = []
    chunks = re.split(r"(?m)^### ", section)
    for chunk in chunks[1:]:
        slug, _, rest = chunk.partition("\n")
        slug = slug.strip()
        if _SLUG.match(slug) is None:
            raise OpencoError(f"entry slug is not lowercase kebab-case: {slug!r}")
        fields: dict[str, str] = {}
        body_lines: list[str] = []
        started = False
        for line in rest.splitlines():
            match = _FIELD_LINE.match(line)
            if not started and not line.strip():
                continue
            if not started and match and match.group(1) in _ENTRY_FIELDS:
                fields[match.group(1)] = match.group(2).strip()
                continue
            started = True
            body_lines.append(line)
        if "title" not in fields:
            raise OpencoError(f"entry {slug} needs a title line")
        body = "\n".join(body_lines).strip()
        if not body:
            raise OpencoError(f"entry {slug} needs a body")
        items.append((slug, fields, body))
    return items
