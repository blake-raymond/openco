"""Check dated, append-only brain files and reject secrets in git."""

import argparse
import sys
import tempfile
from pathlib import Path

from openco.bootstrap import main as bootstrap_main
from openco.config import configured_data_repo
from openco.errors import OpencoError
from openco.format import (
    LOGS,
    RECORD_DIRS,
    check_log,
    check_record,
    is_append,
    normalize,
)
from openco.gitutil import interesting_files, rev_parse, run, show_text
from openco.intake import ingest_file
from openco.paths import ROOT, TEMPLATES
from openco.scan import scan_file, scan_text

PUBLIC_PREFIX = "templates/openco-data"
FROZEN_PUBLIC = ("skills/example-make-tea/SKILL.md",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts/validate")
    parser.add_argument("--selfcheck", action="store_true")
    parser.add_argument("--data-repo", help="private openco-data checkout to check")
    args = parser.parse_args(argv)
    errors: list[str] = []
    errors.extend(check_public())
    data_repo = _data_repo(args.data_repo)
    if data_repo is not None:
        errors.extend(check_data_repo(data_repo))
    if args.selfcheck:
        errors.extend(selfcheck())
    if errors:
        print(f"{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("validate ok")
    return 0


def check_public() -> list[str]:
    errors = check_tree(TEMPLATES, require_example=True, label=PUBLIC_PREFIX)
    errors.extend(_history(ROOT, PUBLIC_PREFIX, LOGS, _record_rels(TEMPLATES)))
    errors.extend(_history(ROOT, "", (), FROZEN_PUBLIC))
    errors.extend(_scan_repo(ROOT))
    errors.extend(_public_rules())
    return errors


def check_data_repo(data_repo: Path) -> list[str]:
    if not data_repo.is_dir():
        return [f"data repo does not exist: {data_repo}"]
    label = str(data_repo)
    errors = check_tree(data_repo, require_example=False, label=label)
    errors.extend(_history(data_repo, "", LOGS, _record_rels(data_repo)))
    errors.extend(_scan_repo(data_repo))
    return errors


def check_tree(root: Path, require_example: bool, label: str) -> list[str]:
    errors: list[str] = []
    for relative in LOGS:
        path = root / relative
        if not path.is_file():
            errors.append(f"{label}/{relative}: missing log")
            continue
        errors.extend(
            _with_label(label, check_log(relative, path.read_text(encoding="utf-8"), require_example))
        )
    for relative in _record_rels(root):
        path = root / relative
        errors.extend(
            _with_label(
                label,
                check_record(relative, path.read_text(encoding="utf-8"), require_example),
            )
        )
    return errors


def selfcheck() -> list[str]:
    errors: list[str] = []
    secret = "AKIA" + "IOSFODNN7EXAMPLE"
    if not scan_text("sample.txt", f"token={secret}\n"):
        errors.append("scanner missed an access key")
    if scan_text("sample.txt", "write to person@example.com\n"):
        errors.append("scanner flagged an example.com address")
    if not scan_text("sample.txt", "write to person@" + "realco.test\n"):
        errors.append("scanner missed a non-example address")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "openco-data"
            bootstrap_main(
                ["--dest", str(dest), "--example-identity", "--no-pointer", "--quiet"]
            )
            note = dest / "inbox" / "examples" / "2026-11-15-example-morning-note.md"
            meeting = dest / "inbox" / "examples" / "2026-11-15-example-meeting.md"
            ingest_file(dest, note)
            ingest_file(dest, meeting)
            errors.extend(check_data_repo(dest))
            facts = (dest / "facts" / "FACTS.md").read_text(encoding="utf-8")
            stories = (dest / "stories" / "STORIES.md").read_text(encoding="utf-8")
            decisions = (dest / "company-brain" / "decisions" / "DECISIONS.md").read_text(
                encoding="utf-8"
            )
            if "example-demo-tea" not in facts or "example-call-length" not in facts:
                errors.append("ingest did not append the sample facts")
            if "example-demo-cafe-story" not in stories:
                errors.append("ingest did not append the sample story")
            if "example-keep-tea-time" not in decisions:
                errors.append("ingest did not append the sample decision")
            transcript = dest / "transcripts" / "2026-11-15-example-morning-note.md"
            if not transcript.is_file():
                errors.append("ingest did not archive the voice note")
            try:
                ingest_file(dest, note)
            except OpencoError:
                pass
            else:
                errors.append("filing the same note twice was allowed")
            log = dest / "facts" / "FACTS.md"
            original = log.read_text(encoding="utf-8")
            log.write_text(original.replace("0 paid staff", "3 paid staff", 1), encoding="utf-8")
            edited = check_data_repo(dest)
            log.write_text(original, encoding="utf-8")
            if not any("append-only" in item for item in edited):
                errors.append("validator allowed an edit inside an old fact")
    except OpencoError as exc:
        errors.append(f"selfcheck: {exc}")
    return errors


def _history(
    repo: Path,
    prefix: str,
    logs: tuple[str, ...] | list[str],
    frozen: tuple[str, ...] | list[str],
) -> list[str]:
    errors: list[str] = []
    for old_rev, new_rev in _pairs(repo):
        for relative in logs:
            gitpath = f"{prefix}/{relative}" if prefix else relative
            errors.extend(_compare(repo, gitpath, old_rev, new_rev, append=True))
        for relative in frozen:
            gitpath = f"{prefix}/{relative}" if prefix else relative
            errors.extend(_compare(repo, gitpath, old_rev, new_rev, append=False))
    return errors


def _compare(repo: Path, gitpath: str, old_rev: str, new_rev: str | None, append: bool) -> list[str]:
    old = show_text(repo, f"{old_rev}:{gitpath}")
    if new_rev is None:
        full = repo / gitpath
        new = full.read_text(encoding="utf-8") if full.is_file() else None
        label = "working tree"
    else:
        new = show_text(repo, f"{new_rev}:{gitpath}")
        label = new_rev[:7]
    if old is None:
        return []
    if new is None:
        return [f"{gitpath}: deleted since {old_rev[:7]} ({label})"]
    if append:
        if not is_append(old, new):
            return [f"{gitpath}: append-only violation since {old_rev[:7]} ({label})"]
        return []
    if normalize(old) != normalize(new):
        return [f"{gitpath}: existing entry was edited since {old_rev[:7]} ({label})"]
    return []


def _pairs(repo: Path) -> list[tuple[str, str | None]]:
    head = rev_parse(repo, "HEAD")
    if head is None:
        return []
    pairs: list[tuple[str, str | None]] = []
    base = rev_parse(repo, "origin/main")
    if base and base != head:
        log = run(repo, ["rev-list", "--reverse", f"{base}..{head}"], check=False)
        parent = base
        if log.returncode == 0:
            for commit in log.stdout.splitlines():
                pairs.append((parent, commit))
                parent = commit
    else:
        parent = rev_parse(repo, "HEAD^")
        if parent:
            pairs.append((parent, head))
    pairs.append((head, None))
    return pairs


def _record_rels(root: Path) -> list[str]:
    found: list[str] = []
    for directory in RECORD_DIRS:
        folder = root / directory
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*.md")):
            if path.name == "README.md":
                continue
            found.append(path.relative_to(root).as_posix())
    return found


def _scan_repo(repo: Path) -> list[str]:
    errors: list[str] = []
    if not (repo / ".git").exists():
        return errors
    for relative in interesting_files(repo):
        path = repo / relative
        if not path.is_file():
            continue
        errors.extend(scan_file(path))
    return errors


def _public_rules() -> list[str]:
    errors: list[str] = []
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if "AGENTS.md" not in claude:
        errors.append("CLAUDE.md must point at AGENTS.md")
    for phrase in ("before any task", "Do not overwrite", "FACTS.md", "EXAMPLE"):
        if phrase not in agents:
            errors.append(f"AGENTS.md is missing {phrase!r}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    for phrase in ("openco-data", "blake-raymond/openco"):
        if phrase not in readme:
            errors.append(f"README.md is missing {phrase}")
    old_repo = "blake-raymond/" + "company"
    if old_repo in readme or old_repo in roadmap:
        errors.append("docs still name the old GitHub repository")
    skill = ROOT / "skills" / "example-make-tea" / "SKILL.md"
    if not skill.is_file() or "EXAMPLE" not in skill.read_text(encoding="utf-8"):
        errors.append("skills/example-make-tea/SKILL.md must stay an obvious example")
    for relative in interesting_files(ROOT):
        if relative.startswith("openco-data/") or relative.startswith(".openco/"):
            errors.append(f"private data path is tracked: {relative}")
        if Path(relative).name == ".env":
            errors.append(f"env file is tracked: {relative}")
    return errors


def _data_repo(explicit: str | None) -> Path | None:
    return configured_data_repo(explicit)


def _with_label(label: str, errors: list[str]) -> list[str]:
    return [f"{label}/{error}" if not error.startswith(label) else error for error in errors]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OpencoError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
