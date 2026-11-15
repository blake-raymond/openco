"""Clone pinned skill repos into skills/vendor/. Do not commit the clones."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from openco.errors import OpencoError
from openco.paths import ROOT

LOCK = ROOT / "skills" / "vendor" / "lock.json"
VENDOR = ROOT / "skills" / "vendor"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    check_only = "--check" in args
    repos = load_lock()
    if check_only:
        print(f"lockfile ok ({len(repos)} repos)")
        return 0
    for repo in repos:
        dest = VENDOR / repo["name"]
        _clone(repo["url"], repo["sha"], dest)
        print(f"installed {repo['name']} at {repo['sha'][:12]}")
    print("clones are gitignored. Do not commit them.")
    return 0


def load_lock(path: Path | None = None) -> list[dict]:
    lock_path = path or LOCK
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OpencoError(f"skills lockfile is unreadable: {exc}") from exc
    repos = data.get("repos")
    if not isinstance(repos, list) or len(repos) != 4:
        raise OpencoError("skills lockfile must pin exactly four repos")
    names = [item.get("name") for item in repos]
    expected = {"anthropics-skills", "superpowers", "mattpocock-skills", "agent-skills"}
    if set(names) != expected:
        raise OpencoError("skills lockfile is missing one of the four packs")
    for item in repos:
        sha = str(item.get("sha", ""))
        url = str(item.get("url", ""))
        if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
            raise OpencoError(f"{item.get('name')}: sha must be 40 hex characters")
        if not url.startswith("https://github.com/") or not url.endswith(".git"):
            raise OpencoError(f"{item.get('name')}: url must be a https://github.com git URL")
        if not item.get("contains"):
            raise OpencoError(f"{item.get('name')}: lockfile entry needs a contains note")
    return repos


def _clone(url: str, sha: str, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _git(["clone", "--filter=blob:none", "--no-checkout", url, str(dest)])
    _git(["fetch", "--depth", "1", "origin", sha], cwd=dest)
    _git(["checkout", "--detach", sha], cwd=dest)


def _git(args: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OpencoError(detail or f"git {' '.join(args)} failed")
