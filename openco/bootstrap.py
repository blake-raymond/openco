"""Create the private openco-data repository from the committed skeleton."""

import os
import shutil
import sys
from pathlib import Path

from openco.errors import OpencoError
from openco.gitutil import commit, rev_parse, run
from openco.paths import DEFAULT_DATA_REPO, POINTER, ROOT, TEMPLATES


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    dest_arg = None
    example_identity = False
    write_pointer = True
    quiet = False
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--dest":
            index += 1
            if index >= len(args):
                raise OpencoError("--dest needs a path")
            dest_arg = args[index]
        elif item == "--example-identity":
            example_identity = True
        elif item == "--no-pointer":
            write_pointer = False
        elif item == "--quiet":
            quiet = True
        else:
            raise OpencoError(f"unknown argument {item}")
        index += 1
    raw = dest_arg or os.environ.get("OPENCO_DATA_REPO") or str(DEFAULT_DATA_REPO)
    dest = _resolve_dest(raw)
    _refuse_inside_public_repo(dest)
    _ensure_skeleton(dest)
    if rev_parse(dest, "HEAD") is None:
        if not (dest / ".git").is_dir():
            run(dest, ["init", "-b", "main"])
        _ensure_identity(dest, example_identity)
        commit(dest, "Initialize openco-data skeleton")
        if not quiet:
            print(f"created private data repo {dest}")
    else:
        if not quiet:
            print(f"private data repo already set up at {dest}")
    if write_pointer:
        _write_pointer(dest)
        if not quiet:
            print(f"this checkout points at it via {POINTER.relative_to(ROOT)}")
    if not quiet:
        print("next: python3 scripts/ingest inbox/examples/2026-11-15-example-morning-note.md")
    return 0


def _resolve_dest(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()


def _refuse_inside_public_repo(dest: Path) -> None:
    if dest == ROOT or ROOT in dest.parents:
        raise OpencoError(
            f"{dest} is inside the public openco repo. "
            "Put openco-data next to it, or pass --dest."
        )


def _ensure_skeleton(dest: Path) -> None:
    marker = dest / ".openco-skeleton"
    if marker.is_file():
        return
    if dest.exists() and any(dest.iterdir()):
        raise OpencoError(f"{dest} is not empty and is not an openco-data checkout")
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)
    marker.write_text("name=openco-data\nskeleton=1\nsource=openco\n", encoding="utf-8")


def _ensure_identity(dest: Path, example_identity: bool) -> None:
    if example_identity:
        run(dest, ["config", "user.email", "openco-setup@example.com"])
        run(dest, ["config", "user.name", "openco setup"])
        run(dest, ["config", "commit.gpgsign", "false"])
        return
    email = run(dest, ["config", "user.email"], check=False)
    name = run(dest, ["config", "user.name"], check=False)
    if email.returncode != 0 or not email.stdout.strip() or name.returncode != 0 or not name.stdout.strip():
        raise OpencoError(
            "git user.name and user.email are not set. "
            "Set them, then run make setup again in the same directory."
        )


def _write_pointer(dest: Path) -> None:
    POINTER.parent.mkdir(parents=True, exist_ok=True)
    POINTER.write_text(str(dest) + "\n", encoding="utf-8")
