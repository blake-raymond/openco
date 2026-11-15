"""Turn a structured recording into a SKILL.md on a branch.

The recording has to already contain When to use, Steps, Checks, and
Mistakes. The skill file tells the agent how to draft those from a raw
transcript. This script does not invent the steps, and it does not
commit to main.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from openco.config import configured_data_repo
from openco.errors import OpencoError
from openco.gitutil import commit, run
from openco.intake import open_pull_request

_SECTIONS = ("When to use", "Steps", "Checks", "Mistakes")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    recording = None
    name = None
    data_arg = None
    no_pr = False
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--name":
            index += 1
            name = args[index] if index < len(args) else None
        elif item == "--data-repo":
            index += 1
            data_arg = args[index] if index < len(args) else None
        elif item == "--no-pr":
            no_pr = True
        elif item.startswith("-"):
            raise OpencoError(f"unknown argument {item}")
        elif recording is None:
            recording = item
        else:
            raise OpencoError("usage: scripts/skill-from-recording RECORDING --name SLUG")
        index += 1
    if not recording or not name:
        raise OpencoError("usage: scripts/skill-from-recording RECORDING --name SLUG")
    if _SLUG.match(name) is None:
        raise OpencoError("--name must be a lowercase slug")
    data_repo = configured_data_repo(data_arg)
    if data_repo is None or not data_repo.is_dir():
        raise OpencoError("no private data repo. Run make setup or pass --data-repo.")
    skill = render_skill(Path(recording).read_text(encoding="utf-8"), name, Path(recording).name)
    status = run(data_repo, ["status", "--porcelain"]).stdout.strip()
    if status:
        raise OpencoError("data repo has uncommitted changes. Commit or stash them first.")
    branch = f"skill/{name}"
    run(data_repo, ["checkout", "-b", branch])
    dest = data_repo / "skills" / name / "SKILL.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(skill, encoding="utf-8")
    commit(data_repo, f"Add skill {name} from a recording", [f"skills/{name}/SKILL.md"])
    current = run(data_repo, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if current in {"main", "master"}:
        raise OpencoError("refusing to leave a commit on main")
    print(f"wrote skills/{name}/SKILL.md on {current}")
    if no_pr:
        return 0
    open_pull_request(
        data_repo,
        current,
        f"Add skill {name}",
        "Drafted from a recording. Check the steps against the recording before merging.\n",
    )
    return 0


def render_skill(text: str, name: str, source_name: str) -> str:
    sections = _sections(text)
    missing = [heading for heading in _SECTIONS if not sections.get(heading, "").strip()]
    if missing:
        raise OpencoError(
            "recording is missing " + ", ".join(missing) + ". Draft those sections from the transcript first."
        )
    description = sections["When to use"].strip().splitlines()[0]
    body = [f"---", f"name: {name}", f"description: {description}", "---", "", f"# {name}", ""]
    for heading in _SECTIONS:
        body.append(f"## {heading}")
        body.append(sections[heading].strip())
        body.append("")
    body.append(f"source: recordings/{source_name}")
    body.append("")
    return "\n".join(body)


def _sections(text: str) -> dict[str, str]:
    chunks = re.split(r"(?m)^## ", text)
    found: dict[str, str] = {}
    for chunk in chunks[1:]:
        heading, _, rest = chunk.partition("\n")
        found[heading.strip()] = rest
    return found
