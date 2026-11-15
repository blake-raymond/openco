"""File inbox notes into facts, stories, and decisions.

The commit is always on a new branch. It is never made on main.
A pull request is opened when the data repo has an origin remote.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from openco.config import configured_data_repo
from openco.errors import OpencoError
from openco.gitutil import commit, run

_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    data_arg = None
    no_pr = False
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--data-repo":
            index += 1
            if index >= len(args):
                raise OpencoError("--data-repo needs a path")
            data_arg = args[index]
        elif item == "--no-pr":
            no_pr = True
        else:
            raise OpencoError(f"unknown argument {item}")
        index += 1
    data_repo = configured_data_repo(data_arg)
    if data_repo is None or not data_repo.is_dir():
        raise OpencoError("no private data repo. Run make setup or pass --data-repo.")
    notes = _notes(data_repo)
    if not notes:
        print("nothing to file")
        return 0
    _require_clean(data_repo)
    branch = _branch_name(notes)
    run(data_repo, ["checkout", "-b", branch])
    written: list[str] = []
    for note in notes:
        written.extend(file_note(data_repo, note))
    commit(data_repo, f"File {len(notes)} inbox note(s)", written)
    current = run(data_repo, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if current in {"main", "master"}:
        raise OpencoError("refusing to leave a commit on main")
    print(f"committed on {current}")
    if no_pr:
        return 0
    opened = open_pull_request(
        data_repo,
        current,
        f"File {len(notes)} inbox note(s)",
        "Filed by scripts/intake. Review the new fact lines before merging.\n",
    )
    if opened:
        print("opened a pull request against main")
    return 0


def file_note(data_repo: Path, note: Path) -> list[str]:
    text = note.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    meta, body = _frontmatter(text)
    date = meta.get("date")
    if not isinstance(date, str) or _DATE.match(date) is None:
        raise OpencoError(f"{note.name}: front matter date must be YYYY-MM-DD")
    sections = _sections(body)
    in_calls = note.parent.name == "calls"
    if in_calls:
        source_rel = f"calls/{note.name}"
    elif _is_transcript(meta):
        source_rel = _copy_transcript(data_repo, note, text, date, meta)
    else:
        source_rel = f"inbox/filed/{note.name}"
    written: list[str] = []
    if not in_calls and _is_transcript(meta):
        written.append(source_rel)
    for line in _bullets(sections.get("facts", "")):
        written.append(_append(data_repo / "facts.md", f"- {date} | source: {source_rel} | {line}"))
    for line in _bullets(sections.get("stories", "")):
        written.append(_append(data_repo / "stories.md", f"- {date} | {line}"))
    for slug, fields in _decisions(sections.get("decisions", "")):
        relative = f"decisions/{date}-{slug}.md"
        path = data_repo / relative
        if path.exists():
            raise OpencoError(f"{relative} already exists")
        path.write_text(
            _decision_file(date, fields, meta.get("example") is True, source_rel),
            encoding="utf-8",
        )
        written.append(relative)
    if in_calls:
        return written
    filed_rel = f"inbox/filed/{note.name}"
    filed_path = data_repo / filed_rel
    if filed_path.exists():
        raise OpencoError(f"{filed_rel} already exists")
    filed_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(note), str(filed_path))
    written.append(filed_rel)
    old = f"inbox/{note.name}"
    if run(data_repo, ["ls-files", "--", old]).stdout.strip():
        written.append(old)
    return written


def open_pull_request(data_repo: Path, branch: str, title: str, body: str) -> bool:
    remotes = run(data_repo, ["remote"]).stdout.split()
    if "origin" not in remotes:
        print(f"branch {branch} is ready. There is no origin remote, so no pull request was opened.")
        return False
    run(data_repo, ["push", "-u", "origin", branch])
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body", body],
        cwd=data_repo,
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OpencoError(detail or "gh pr create failed")
    if result.stdout.strip():
        print(result.stdout.strip())
    return True


def _notes(data_repo: Path) -> list[Path]:
    notes: list[Path] = []
    inbox = data_repo / "inbox"
    if inbox.is_dir():
        notes.extend(path for path in sorted(inbox.glob("*.md")) if path.name != "README.md")
    calls = data_repo / "calls"
    if calls.is_dir():
        linked = _linked_calls(data_repo)
        for path in sorted(calls.glob("*.md")):
            if path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8")
            if "## Facts" not in text and "## Decisions" not in text and "## Stories" not in text:
                continue
            if f"calls/{path.name}" in linked:
                continue
            notes.append(path)
    return notes


def _linked_calls(data_repo: Path) -> str:
    parts = [(data_repo / "facts.md").read_text(encoding="utf-8")]
    decisions = data_repo / "decisions"
    if decisions.is_dir():
        parts.extend(path.read_text(encoding="utf-8") for path in decisions.glob("*.md"))
    return "\n".join(parts)


def _branch_name(notes: list[Path]) -> str:
    if len(notes) == 1:
        return "intake/" + notes[0].stem
    return "intake/" + notes[0].stem[:10] + "-notes"


def _require_clean(data_repo: Path) -> None:
    status = run(data_repo, ["status", "--porcelain"]).stdout.strip()
    if status:
        raise OpencoError("data repo has uncommitted changes. Commit or stash them before intake.")


def _append(path: Path, line: str) -> str:
    text = path.read_text(encoding="utf-8")
    if line in text.splitlines():
        raise OpencoError(f"already filed: {line}")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n", encoding="utf-8")
    return path.name if path.name != "DECISIONS.md" else str(path)


def _is_transcript(meta: dict[str, object]) -> bool:
    return meta.get("kind") in {"transcript", "meeting"}


def _copy_transcript(data_repo: Path, note: Path, text: str, date: str, meta: dict[str, object]) -> str:
    title = str(meta.get("title") or note.stem)
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:60].strip("-")
    if _SLUG.match(slug or "") is None:
        raise OpencoError(f"{note.name}: transcript title did not produce a file name")
    relative = f"calls/{date}-{slug}.md"
    path = data_repo / relative
    if path.exists():
        raise OpencoError(f"{relative} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return relative


def _decision_file(date: str, fields: dict[str, str], example: bool, source: str) -> str:
    status = fields.get("status") or "proposed"
    lines = [
        "---",
        f"date: {date}",
        f"status: {status}",
        f"source: {source}",
    ]
    if example:
        lines.append("example: true")
    lines.extend(
        [
            "---",
            "",
            f"# {fields['decision']}",
            "",
            "## Context",
            "",
            fields["context"],
            "",
            "## Decision",
            "",
            fields["decision"],
            "",
            "## Why",
            "",
            fields["why"],
            "",
        ]
    )
    return "\n".join(lines)


def _decisions(section: str) -> list[tuple[str, dict[str, str]]]:
    items = []
    chunks = re.split(r"(?m)^### ", section)
    fields_ok = {"status", "context", "decision", "why"}
    for chunk in chunks[1:]:
        slug, _, rest = chunk.partition("\n")
        slug = slug.strip()
        if _SLUG.match(slug) is None:
            raise OpencoError(f"decision slug is not lowercase kebab-case: {slug!r}")
        fields: dict[str, str] = {}
        body: list[str] = []
        started = False
        for line in rest.splitlines():
            if not started and not line.strip():
                continue
            if not started and ":" in line and line.split(":", 1)[0] in fields_ok:
                key, raw = line.split(":", 1)
                fields[key] = raw.strip()
                continue
            started = True
            body.append(line)
        if "decision" not in fields or "why" not in fields:
            raise OpencoError(f"decision {slug} needs decision and why lines")
        if not fields.get("context"):
            fields["context"] = "\n".join(body).strip() or f"Recorded in {slug}."
        items.append((slug, fields))
    return items


def _bullets(section: str) -> list[str]:
    bullets = []
    for line in section.splitlines():
        if line.startswith("- "):
            text = line[2:].strip()
            if text:
                bullets.append(text)
    return bullets


def _sections(body: str) -> dict[str, str]:
    chunks = re.split(r"(?m)^## ", body)
    sections: dict[str, str] = {}
    for chunk in chunks[1:]:
        name, _, rest = chunk.partition("\n")
        sections[name.strip().casefold()] = rest
    return sections


def _frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise OpencoError("inbox note must start with front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise OpencoError("inbox note front matter is not closed")
    meta: dict[str, object] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value: object = raw.strip()
        if value == "true":
            value = True
        elif value == "false":
            value = False
        meta[key.strip()] = value
    return meta, text[end + 5 :]
