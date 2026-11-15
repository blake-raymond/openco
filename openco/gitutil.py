"""Small git helpers. Commands run only in the repository they are given."""

import subprocess
from pathlib import Path

from openco.errors import OpencoError


def run(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OpencoError(detail or f"git {' '.join(args)} failed")
    return result


def rev_parse(repo: Path, ref: str) -> str | None:
    result = run(repo, ["rev-parse", "--verify", ref], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def show_text(repo: Path, spec: str) -> str | None:
    result = run(repo, ["show", spec], check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def tracked_files(repo: Path) -> list[str]:
    if rev_parse(repo, "HEAD") is None:
        return []
    return [line for line in run(repo, ["ls-files"]).stdout.splitlines() if line]


def interesting_files(repo: Path) -> list[str]:
    """Tracked files plus untracked files that are not gitignored."""

    paths = set(tracked_files(repo))
    others = run(repo, ["ls-files", "--others", "--exclude-standard"], check=False)
    if others.returncode == 0:
        paths.update(line for line in others.stdout.splitlines() if line)
    return sorted(paths)


def commit(repo: Path, message: str, paths: list[str] | None = None) -> bool:
    if paths is None:
        run(repo, ["add", "-A"])
    else:
        run(repo, ["add", "--", *paths])
    staged = run(repo, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        return False
    run(repo, ["commit", "-m", message])
    return True
