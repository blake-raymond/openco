"""Check the public repo, the data template, and the intake path."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from openco.bootstrap import main as bootstrap_main
from openco.errors import OpencoError
from openco.granola import convert
from openco.intake import main as intake_main
from openco.paths import ROOT, TEMPLATES
from openco.scan import scan_file, scan_text, transcript_finding

CHECK = TEMPLATES / "scripts" / "check.py"


def main(argv: list[str] | None = None) -> int:
    selfcheck = "--selfcheck" in (argv if argv is not None else sys.argv[1:])
    errors = check_public()
    if selfcheck:
        errors.extend(run_selfcheck())
    if errors:
        print(f"{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("validate ok")
    return 0


def check_public() -> list[str]:
    errors = _run_check(["--root", str(TEMPLATES), "--format-only", "--require-example"])
    errors.extend(_scan_repo(ROOT))
    errors.extend(_public_rules())
    return errors


def run_selfcheck() -> list[str]:
    errors: list[str] = []
    secret = "AKIA" + "IOSFODNN7EXAMPLE"
    if not scan_text("sample.txt", f"token={secret}\n"):
        errors.append("scanner missed an access key")
    if scan_text("sample.txt", "write to person@example.com\n"):
        errors.append("scanner flagged an example.com address")
    if not scan_text("sample.txt", "write to person@" + "realco.test\n"):
        errors.append("scanner missed a non-example address")
    if transcript_finding("calls/2026-11-15-demo.md", "hello") is None:
        errors.append("privacy scan allowed a transcript path")
    if transcript_finding("docs/setup/calls.md", "---\nkind: transcript\n---\n") is not None:
        errors.append("privacy scan flagged the calls setup doc")
    errors.extend(_notion_checks())
    try:
        converted, _markdown = convert(_generic_transcript())
        if converted != "calls/2026-11-15-demo-call.md":
            errors.append(f"generic transcript wrote {converted}")
        try:
            convert("title,summary,transcript\nDemo,None,Hello\n")
        except OpencoError as exc:
            if "columns" not in str(exc):
                errors.append(f"CSV error did not mention the column gap: {exc}")
        else:
            errors.append("CSV export was parsed without a documented column schema")
    except OpencoError as exc:
        errors.append(f"generic transcript: {exc}")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "openco-data"
            bootstrap_main(["--dest", str(dest), "--example-identity", "--no-pointer", "--quiet"])
            bare = root / "origin.git"
            subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=dest, check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=dest, check=True, capture_output=True)
            main_before = subprocess.check_output(["git", "rev-parse", "main"], cwd=dest, text=True).strip()
            gh_log = root / "gh.log"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            gh = bin_dir / "gh"
            gh.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$GH_LOG\"\n", encoding="utf-8")
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            env["GH_LOG"] = str(gh_log)
            (dest / "inbox" / "2026-11-15-example-call.md").write_text(
                "---\n"
                "date: 2026-11-15\n"
                "title: Example call\n"
                "kind: transcript\n"
                "example: true\n"
                "---\n\n"
                "Alex Example: EXAMPLE transcript line.\n\n"
                "## Facts\n\n"
                "- EXAMPLE: the demo call lasted 0 minutes.\n\n"
                "## Decisions\n\n"
                "### example-keep-window\n"
                "decision: EXAMPLE keep the window\n"
                "why: The fictional staff is only there then.\n"
                "supersedes:\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "intake"), "--data-repo", str(dest)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                env=env,
            )
            if result.returncode != 0:
                errors.append(result.stderr.strip() or result.stdout.strip() or "intake failed")
                return errors
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dest, text=True
            ).strip()
            if branch in {"main", "master"}:
                errors.append("intake committed on main")
            if subprocess.check_output(["git", "rev-parse", "main"], cwd=dest, text=True).strip() != main_before:
                errors.append("intake moved main")
            facts = (dest / "facts.md").read_text(encoding="utf-8")
            if "example company serves tea" not in facts or "source: inbox/filed/" not in facts:
                errors.append("intake did not append a sourced fact")
            if not (dest / "decisions" / "2026-11-15-example-keep-tea-time.md").is_file():
                errors.append("intake did not write the decision file")
            story = "- 2026-11-15 | EXAMPLE: Alex Example at Demo Cafe asked for a sample widget."
            if story not in (dest / "stories.md").read_text(encoding="utf-8"):
                errors.append("intake did not append the story")
            call = dest / "calls" / "2026-11-15-example-call.md"
            call_text = call.read_text(encoding="utf-8") if call.is_file() else ""
            if "EXAMPLE transcript line." not in call_text:
                errors.append("intake did not store the raw transcript in calls/")
            if "source: calls/2026-11-15-example-call.md" not in facts:
                errors.append("intake did not link the fact back to the transcript")
            decision = (dest / "decisions" / "2026-11-15-example-keep-window.md").read_text(encoding="utf-8")
            if "source: calls/2026-11-15-example-call.md" not in decision:
                errors.append("intake did not link the decision back to the transcript")
            history = _run_check(["--root", str(dest)])
            if history:
                errors.extend(history)
            original = (dest / "facts.md").read_text(encoding="utf-8")
            (dest / "facts.md").write_text(original.replace("0 paid staff", "3 paid staff", 1), encoding="utf-8")
            edited = _run_check(["--root", str(dest)])
            (dest / "facts.md").write_text(original, encoding="utf-8")
            if not any("append-only" in item for item in edited):
                errors.append("data check allowed an edit to an old fact")
            errors.extend(_notion_snapshot_is_editable(dest))
            recorded = gh_log.read_text(encoding="utf-8") if gh_log.is_file() else ""
            if "--base" not in recorded or "main" not in recorded:
                errors.append("intake did not ask gh to open a pull request against main")
    except (OpencoError, subprocess.CalledProcessError) as exc:
        errors.append(f"selfcheck: {exc}")
    return errors


def _run_check(args: list[str]) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(CHECK), *args],
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return []
    return [line[2:] if line.startswith("- ") else line for line in result.stderr.splitlines() if line.strip()]


def _scan_repo(repo: Path) -> list[str]:
    errors: list[str] = []
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    for relative in sorted(set(listed.stdout.splitlines())):
        path = repo / relative
        if path.is_file():
            errors.extend(scan_file(path))
    return errors


def _public_rules() -> list[str]:
    errors: list[str] = []
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    if "AGENTS.md" not in claude:
        errors.append("CLAUDE.md must point at AGENTS.md")
    for phrase in ("before any task", "Do not overwrite", "facts.md", "EXAMPLE", "without approval"):
        if phrase not in agents:
            errors.append(f"AGENTS.md is missing {phrase!r}")
    for phrase in ("openco-data", "blake-raymond/openco", "templates/data"):
        if phrase not in readme:
            errors.append(f"README.md is missing {phrase}")
    old_repo = "blake-raymond/" + "company"
    if old_repo in readme or old_repo in roadmap:
        errors.append("docs still name the old GitHub repository")
    skill = ROOT / "skills" / "intake" / "SKILL.md"
    if not skill.is_file():
        errors.append("skills/intake/SKILL.md is missing")
    for relative in (
        "docs/setup/wispr.md",
        "docs/setup/granola.md",
        "docs/setup/memory.md",
        "docs/setup/notion-second-brain.md",
    ):
        if not (ROOT / relative).is_file():
            errors.append(f"{relative} is missing")
    return errors


def _notion_checks() -> list[str]:
    from openco.notion_export import export_database
    from openco.second_brain import source

    errors: list[str] = []
    saved = {key: os.environ.get(key) for key in ("SECOND_BRAIN", "NOTION_TOKEN", "NOTION_SECOND_BRAIN_DB")}
    try:
        os.environ["SECOND_BRAIN"] = "notion"
        os.environ["NOTION_TOKEN"] = ""
        os.environ["NOTION_SECOND_BRAIN_DB"] = ""
        if not (ROOT / ".env").is_file() and source() != "markdown":
            errors.append("second brain did not fall back to markdown without Notion")
        os.environ["NOTION_TOKEN"] = "test-token"
        os.environ["NOTION_SECOND_BRAIN_DB"] = "database"
        if source() != "notion":
            errors.append("second brain did not use Notion when configured")
        os.environ["SECOND_BRAIN"] = "markdown"
        if source() != "markdown":
            errors.append("SECOND_BRAIN=markdown was ignored")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    calls: list[str] = []

    def transport(method: str, path: str, body: dict | None) -> dict:
        calls.append(method + " " + path.split("?", 1)[0])
        if method == "GET" and path.startswith("/v1/databases/"):
            return {"data_sources": [{"id": "source-1", "name": "Commonplace book"}]}
        if method == "POST" and path.endswith("/query"):
            return {
                "has_more": False,
                "next_cursor": None,
                "results": [
                    {
                        "object": "page",
                        "id": "page-1",
                        "properties": {
                            "Name": {"type": "title", "title": [{"plain_text": "How I decide"}]}
                        },
                    }
                ],
            }
        if method == "GET" and "/children" in path:
            return {
                "has_more": False,
                "next_cursor": None,
                "results": [
                    {
                        "id": "block-1",
                        "type": "paragraph",
                        "has_children": False,
                        "paragraph": {"rich_text": [{"plain_text": "Reversible when waiting is cheap."}]},
                    }
                ],
            }
        raise OpencoError(f"unexpected Notion call {method} {path}")

    with tempfile.TemporaryDirectory() as tmp:
        written = export_database(Path(tmp), "database", transport)
        text = (Path(tmp) / written[0]).read_text(encoding="utf-8")
        if "Reversible when waiting is cheap." not in text:
            errors.append("notion export dropped the page body")
        if any(call.startswith("PATCH") or call.startswith("DELETE") or call.startswith("PUT") for call in calls):
            errors.append("notion export used a write method")
        if not any(call.startswith("GET /v1/databases/") for call in calls):
            errors.append("notion export did not retrieve the database")
        if not any(call == "POST /v1/data_sources/source-1/query" for call in calls):
            errors.append("notion export did not query the data source")
    return errors


def _notion_snapshot_is_editable(dest: Path) -> list[str]:
    subprocess.run(["git", "checkout", "main"], cwd=dest, check=True, capture_output=True)
    snapshot = dest / "me" / "notion" / "snapshot.md"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text("---\nsource: notion\n---\n\n# EXAMPLE\n\nFirst.\n", encoding="utf-8")
    subprocess.run(["git", "add", "me/notion/snapshot.md"], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", "Add notion snapshot"], cwd=dest, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "notion-update"], cwd=dest, check=True, capture_output=True)
    snapshot.write_text("---\nsource: notion\n---\n\n# EXAMPLE\n\nUpdated.\n", encoding="utf-8")
    subprocess.run(["git", "add", "me/notion/snapshot.md"], cwd=dest, check=True)
    subprocess.run(["git", "commit", "-m", "Update notion snapshot"], cwd=dest, check=True, capture_output=True)
    previous = os.environ.get("BASE_REF")
    os.environ["BASE_REF"] = "main"
    try:
        problems = _run_check(["--root", str(dest)])
    finally:
        if previous is None:
            os.environ.pop("BASE_REF", None)
        else:
            os.environ["BASE_REF"] = previous
    return [item for item in problems if "me/notion" in item]


def _generic_transcript() -> str:
    return (
        "---\n"
        "date: 2026-11-15\n"
        "title: Demo call\n"
        "example: true\n"
        "---\n"
        "\n"
        "Alex Example: This is a fake transcript.\n"
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OpencoError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
