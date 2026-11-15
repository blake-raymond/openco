"""One command that sets up your data repo and resumes where you stopped.

You name the repository. Nothing here assumes a brand. External actions
wait for a yes, except when you pass --yes. The chosen name, remote, and
path are stored in .openco/setup-state.json, which is gitignored.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from openco.bootstrap import ensure_skeleton, refuse_inside_public_repo, resolve_dest, write_pointer
from openco.errors import OpencoError
from openco.gitutil import commit, rev_parse, run
from openco.paths import ROOT, STATE

PLACEHOLDER_NAME = "company-data"
REQUIRED = ("prerequisites", "github-repo", "scaffold", "remote", "push", "ci")
OPTIONAL = ("notion", "calls", "memory", "skills", "mcp")
STEPS = REQUIRED + OPTIONAL
NOTION_LINK = "https://developers.notion.com/docs/create-a-notion-integration"


class Runner:
    def gh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        binary = os.environ.get("OPENCO_GH", "gh")
        return subprocess.run([binary, *args], text=True, capture_output=True)

    def git_push(self, dest: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(dest), "push", "-u", "origin", "main"],
            text=True,
            capture_output=True,
        )


def main(argv: list[str] | None = None, runner: Runner | None = None, input_fn=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    yes = False
    check = False
    with_skills = False
    owner = None
    name = None
    dest_arg = None
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--yes":
            yes = True
        elif item == "--check":
            check = True
        elif item == "--with-skills":
            with_skills = True
        elif item in {"--owner", "--name", "--dest"}:
            index += 1
            if index >= len(args):
                raise OpencoError(f"{item} needs a value")
            if item == "--owner":
                owner = args[index]
            elif item == "--name":
                name = args[index]
            else:
                dest_arg = args[index]
        else:
            raise OpencoError(f"unknown argument {item}")
        index += 1
    commands = runner or Runner()
    reader = input_fn or input
    state = load_state()
    if check:
        _print_check(state, commands)
        return 0
    _step_prerequisites(state, commands)
    owner, name = _step_name(state, commands, yes, owner, name, reader)
    dest = resolve_dest(dest_arg) if dest_arg else _default_dest(name)
    refuse_inside_public_repo(dest)
    remote = f"https://github.com/{owner}/{name}.git"
    _remember(state, owner, name, remote, dest)
    _step_github(state, commands, yes, owner, name, reader)
    _step_scaffold(state, dest, name)
    _step_remote(state, dest, remote, yes, reader)
    _step_push(state, commands, dest, yes, reader)
    _step_ci(state, commands, owner, name, yes, reader)
    _step_notion(state, yes, reader)
    _step_calls(state, yes, reader)
    _step_memory(state, yes, reader)
    _step_skills(state, yes, with_skills, reader)
    _step_mcp(state, yes, reader)
    save_state(state)
    print(f"Your data repo is {dest}")
    print('Run make setup again to resume. make setup ARGS="--check" reports status.')
    return 0


def load_state() -> dict:
    if not STATE.is_file():
        return {"steps": {}, "data_repo": {}}
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OpencoError(f"setup state is not valid JSON: {STATE}") from exc
    data.setdefault("steps", {})
    data.setdefault("data_repo", {})
    return data


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _print_check(state: dict, commands: Runner) -> None:
    record = state.get("data_repo") or {}
    probes = {
        "prerequisites": "done" if _prereqs_ok(commands) else "missing",
        "scaffold": "done"
        if record.get("path") and (Path(record["path"]) / ".openco-skeleton").is_file()
        else "missing",
        "remote": "done" if _remote_matches(record) else "missing",
    }
    for step in STEPS:
        recorded = state.get("steps", {}).get(step)
        if step in probes and probes[step] == "missing" and recorded != "skipped":
            status = "missing"
        elif recorded:
            status = recorded
        elif step in probes:
            status = probes[step]
        else:
            status = "missing"
        extra = ""
        if step == "github-repo" and record.get("owner") and record.get("name"):
            extra = f" ({record['owner']}/{record['name']})"
        print(f"{step}: {status}{extra}")


def _step_prerequisites(state: dict, commands: Runner) -> None:
    print("Check that git, Python, and the GitHub CLI are installed, and that gh is logged in.")
    if _prereqs_ok(commands):
        state["steps"]["prerequisites"] = "done"
        save_state(state)
        return
    missing = []
    if shutil.which("git") is None:
        missing.append("git")
    if shutil.which("python3") is None:
        missing.append("python3")
    if shutil.which(os.environ.get("OPENCO_GH", "gh")) is None:
        missing.append("gh (https://cli.github.com)")
    else:
        auth = commands.gh(["auth", "status"])
        if auth.returncode != 0:
            missing.append("gh auth login")
    raise OpencoError("missing " + ", ".join(missing))


def _step_name(state, commands, yes, owner, name, reader) -> tuple[str, str]:
    record = state.get("data_repo") or {}
    if record.get("owner") and record.get("name") and not owner and not name:
        print(f"Use your data repo {record['owner']}/{record['name']}.")
        return record["owner"], record["name"]
    suggested = _gh_login(commands)
    if yes:
        if not name:
            raise OpencoError("pass --name. There is no built-in repository name.")
        owner = owner or suggested
        if not owner:
            raise OpencoError("pass --owner. gh could not see a logged-in user.")
        print(f"Repository {owner}/{name}.")
        return owner, name
    print("Choose the GitHub owner and name for your data repo.")
    print("The name placeholder is company-data. Press enter to confirm it, or type your own.")
    typed_owner = reader(f"Owner [{suggested}]: ").strip()
    typed_name = reader("Name [company-data]: ").strip()
    owner = typed_owner or owner or suggested
    name = typed_name or name or PLACEHOLDER_NAME
    if not owner or not name:
        raise OpencoError("owner and name are required")
    return owner, name


def _step_github(state, commands, yes, owner, name, reader) -> None:
    if state["steps"].get("github-repo") == "done" and _repo_exists(commands, owner, name):
        print(f"Private repository {owner}/{name} is already there.")
        return
    print(f"Create a private GitHub repository named {owner}/{name}.")
    if not _confirm(f"Create {owner}/{name} as private?", yes, reader):
        raise OpencoError("stopped before creating the repository. Run make setup to continue.")
    if not _repo_exists(commands, owner, name):
        created = commands.gh(
            ["repo", "create", f"{owner}/{name}", "--private", "--description", "Private notes"]
        )
        if created.returncode != 0:
            detail = (created.stderr or created.stdout).strip()
            raise OpencoError(detail or "gh repo create failed")
    state["steps"]["github-repo"] = "done"
    save_state(state)


def _step_scaffold(state, dest: Path, name: str) -> None:
    if state["steps"].get("scaffold") == "done" and (dest / ".openco-skeleton").is_file() and rev_parse(dest, "HEAD"):
        print(f"Template is already in {dest}.")
        write_pointer(dest)
        return
    print(f"Copy the template into {dest} and make the first local commit.")
    ensure_skeleton(dest, name)
    if rev_parse(dest, "HEAD") is None:
        if not (dest / ".git").is_dir():
            run(dest, ["init", "-b", "main"])
        _local_identity(dest)
        commit(dest, "Initialize data repo skeleton")
    write_pointer(dest)
    state["steps"]["scaffold"] = "done"
    save_state(state)


def _step_remote(state, dest, remote, yes, reader) -> None:
    current = _origin_url(dest)
    if current == remote:
        state["steps"]["remote"] = "done"
        save_state(state)
        print(f"origin already points at {remote}.")
        return
    print(f"Point origin at {remote}.")
    if not _confirm(f"Add origin {remote}?", yes, reader):
        raise OpencoError("stopped before adding the remote. Run make setup to continue.")
    if current:
        run(dest, ["remote", "set-url", "origin", remote])
    else:
        run(dest, ["remote", "add", "origin", remote])
    state["steps"]["remote"] = "done"
    save_state(state)


def _step_push(state, commands, dest, yes, reader) -> None:
    if state["steps"].get("push") == "done":
        print("main is already pushed.")
        return
    print("Push main so your data repo has the template and its checks.")
    if not _confirm("Push main to origin?", yes, reader):
        raise OpencoError("stopped before pushing. Run make setup to continue.")
    pushed = commands.git_push(dest)
    if pushed.returncode != 0:
        detail = (pushed.stderr or pushed.stdout).strip()
        raise OpencoError(detail or "git push failed")
    state["steps"]["push"] = "done"
    save_state(state)


def _step_ci(state, commands, owner, name, yes, reader) -> None:
    if state["steps"].get("ci") == "done":
        print("The check workflow is already enabled.")
        return
    print("Enable the check workflow on your data repo.")
    if not _confirm("Enable the check workflow?", yes, reader):
        raise OpencoError("stopped before enabling checks. Run make setup to continue.")
    enabled = commands.gh(["workflow", "enable", "check.yml", "--repo", f"{owner}/{name}"])
    if enabled.returncode != 0:
        detail = (enabled.stderr or enabled.stdout).strip()
        raise OpencoError(detail or "could not enable the workflow")
    state["steps"]["ci"] = "done"
    save_state(state)


def _step_notion(state, yes, reader) -> None:
    if state["steps"].get("notion") == "done":
        print("Notion token is already in .env.")
        return
    print("Optional: save a Notion token and database id in the gitignored .env file.")
    token_ready = bool(os.environ.get("NOTION_TOKEN", "").strip() and os.environ.get("NOTION_SECOND_BRAIN_DB", "").strip())
    if yes and not token_ready:
        state["steps"]["notion"] = "skipped"
        print("Skipped Notion. me/ is the fallback until you add a token.")
        save_state(state)
        return
    if not yes and not _confirm("Set up Notion now?", False, reader):
        state["steps"]["notion"] = "skipped"
        save_state(state)
        return
    if not yes:
        print(f"Open {NOTION_LINK}")
        print("Create a token, share your database with it, then paste the two values. They are not printed back.")
        token = reader("NOTION_TOKEN: ").strip()
        database = reader("NOTION_SECOND_BRAIN_DB: ").strip()
    else:
        token = os.environ["NOTION_TOKEN"].strip()
        database = os.environ["NOTION_SECOND_BRAIN_DB"].strip()
    if not token or not database:
        raise OpencoError("Notion needs both a token and a database id")
    _upsert_env("SECOND_BRAIN", "notion")
    _upsert_env("NOTION_TOKEN", token)
    _upsert_env("NOTION_SECOND_BRAIN_DB", database)
    state["steps"]["notion"] = "done"
    save_state(state)


def _step_calls(state, yes, reader) -> None:
    if state["steps"].get("calls") == "done":
        return
    print("Calls: you drop a generic transcript in your data repo later. See docs/setup/calls.md.")
    if yes or _confirm("Mark call setup done?", False, reader):
        state["steps"]["calls"] = "done"
    else:
        state["steps"]["calls"] = "skipped"
    save_state(state)


def _step_memory(state, yes, reader) -> None:
    if state["steps"].get("memory") == "done":
        return
    print("Memory is the memory/ folder in your data repo. Nothing else to install.")
    if yes or _confirm("Use memory/ as your memory?", False, reader):
        state["steps"]["memory"] = "done"
    else:
        state["steps"]["memory"] = "skipped"
    save_state(state)


def _step_skills(state, yes, with_skills, reader) -> None:
    if state["steps"].get("skills") == "done":
        print("Skill packs are already installed.")
        return
    print("Optional: clone the four pinned skill packs into skills/vendor/.")
    do_it = with_skills or (not yes and _confirm("Install skill packs now?", False, reader))
    if not do_it:
        state["steps"]["skills"] = "skipped"
        save_state(state)
        return
    from openco.install_skills import main as install_main

    install_main([])
    state["steps"]["skills"] = "done"
    save_state(state)


def _step_mcp(state, yes, reader) -> None:
    if state["steps"].get("mcp") == "done":
        return
    print("MCP secrets stay in .env. config/mcp.example.json leaves them empty. See docs/setup/mcp.md.")
    if yes or not _confirm("Mark MCP setup done?", False, reader):
        state["steps"]["mcp"] = "skipped"
        save_state(state)
        return
    state["steps"]["mcp"] = "done"
    save_state(state)


def _confirm(prompt: str, yes: bool, reader) -> bool:
    if yes:
        print(f"{prompt} yes")
        return True
    answer = reader(f"{prompt} [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _prereqs_ok(commands: Runner) -> bool:
    if shutil.which("git") is None or shutil.which("python3") is None:
        return False
    if shutil.which(os.environ.get("OPENCO_GH", "gh")) is None:
        return False
    return commands.gh(["auth", "status"]).returncode == 0


def _gh_login(commands: Runner) -> str:
    result = commands.gh(["api", "user", "--jq", ".login"])
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _repo_exists(commands: Runner, owner: str, name: str) -> bool:
    return commands.gh(["repo", "view", f"{owner}/{name}", "--json", "name"]).returncode == 0


def _origin_url(dest: Path) -> str:
    """The URL stored in git config, not the credential rewrite of it."""

    current = run(dest, ["config", "--get", "remote.origin.url"], check=False)
    if current.returncode != 0:
        return ""
    return current.stdout.strip()


def _remote_matches(record: dict) -> bool:
    path = record.get("path")
    remote = record.get("remote")
    if not path or not remote:
        return False
    dest = Path(path)
    if not (dest / ".git").exists():
        return False
    return _origin_url(dest) == remote


def _default_dest(name: str) -> Path:
    return (ROOT.parent / name).resolve()


def _remember(state, owner, name, remote, dest: Path) -> None:
    state["data_repo"] = {"owner": owner, "name": name, "remote": remote, "path": str(dest)}
    save_state(state)


def _local_identity(dest: Path) -> None:
    email = os.environ.get("GIT_AUTHOR_EMAIL", "").strip()
    person = os.environ.get("GIT_AUTHOR_NAME", "").strip()
    if email and person:
        run(dest, ["config", "user.email", email])
        run(dest, ["config", "user.name", person])
        run(dest, ["config", "commit.gpgsign", "false"])
        return
    configured_email = run(dest, ["config", "user.email"], check=False)
    configured_name = run(dest, ["config", "user.name"], check=False)
    if (
        configured_email.returncode != 0
        or not configured_email.stdout.strip()
        or configured_name.returncode != 0
        or not configured_name.stdout.strip()
    ):
        raise OpencoError("Set git user.name and user.email, then run make setup again.")


def _upsert_env(key: str, value: str) -> None:
    path = ROOT / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    output = []
    found = False
    prefix = key + "="
    for line in lines:
        if line.startswith(prefix):
            output.append(prefix + value)
            found = True
        else:
            output.append(line)
    if not found:
        output.append(prefix + value)
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def wizard_selfcheck() -> list[str]:
    """Run setup against a fake gh. No GitHub repository is created."""

    errors: list[str] = []
    calls: list[list[str]] = []

    class Fake(Runner):
        def __init__(self) -> None:
            self.created = False

        def gh(self, args: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(list(args))
            if args[:2] == ["auth", "status"]:
                return _result(0, "logged in\n")
            if args[:4] == ["api", "user", "--jq", ".login"]:
                return _result(0, "testowner\n")
            if args[:2] == ["repo", "view"]:
                return _result(0 if self.created else 1, "name\n" if self.created else "not found\n")
            if args[:2] == ["repo", "create"]:
                self.created = True
                return _result(0, "created\n")
            if args[:2] == ["workflow", "enable"]:
                return _result(0, "enabled\n")
            return _result(1, "unexpected\n")

        def git_push(self, dest: Path) -> subprocess.CompletedProcess[str]:
            calls.append(["git", "push", "-u", "origin", "main"])
            return _result(0, "pushed\n")

    import tempfile
    from io import StringIO

    saved_state = STATE.read_text(encoding="utf-8") if STATE.is_file() else None
    from openco.paths import POINTER

    saved_pointer = POINTER.read_text(encoding="utf-8") if POINTER.is_file() else None
    saved_env = {
        key: os.environ.get(key)
        for key in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")
    }
    try:
        os.environ["GIT_AUTHOR_NAME"] = "openco setup"
        os.environ["GIT_AUTHOR_EMAIL"] = "openco-setup@example.com"
        os.environ["GIT_COMMITTER_NAME"] = "openco setup"
        os.environ["GIT_COMMITTER_EMAIL"] = "openco-setup@example.com"
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "acme-data"
            fake = Fake()
            try:
                main(["--yes"], runner=fake)
            except OpencoError as exc:
                if "pass --name" not in str(exc):
                    errors.append(f"setup should require --name: {exc}")
            else:
                errors.append("setup used a built-in repository name")
            if main(
                ["--yes", "--name", "acme-data", "--owner", "testowner", "--dest", str(dest)],
                runner=fake,
            ) != 0:
                errors.append("setup --yes failed")
            joined = " ".join(" ".join(call) for call in calls)
            if "repo create testowner/acme-data --private" not in joined:
                errors.append("setup did not create the named private repository")
            banned = "openco-" + "data"
            if banned in joined:
                errors.append("setup used a hardcoded data repo name")
            state = load_state()
            record = state.get("data_repo") or {}
            if record.get("name") != "acme-data" or record.get("remote") != "https://github.com/testowner/acme-data.git":
                errors.append("setup did not store the chosen name and remote")
            marker = dest / ".openco-skeleton"
            if not marker.is_file() or "name=acme-data" not in marker.read_text(encoding="utf-8"):
                errors.append("setup did not record the chosen name in the scaffold")
            before = len([call for call in calls if call[:2] == ["repo", "create"]])
            main(["--yes", "--name", "acme-data", "--owner", "testowner", "--dest", str(dest)], runner=fake)
            after = len([call for call in calls if call[:2] == ["repo", "create"]])
            if after != before:
                errors.append("setup created the repository again on resume")
            buffer = StringIO()
            real_stdout = sys.stdout
            sys.stdout = buffer
            try:
                main(["--check"], runner=fake)
            finally:
                sys.stdout = real_stdout
            report = buffer.getvalue()
            if "github-repo: done (testowner/acme-data)" not in report:
                errors.append("check mode did not report the stored repository")
            if banned in report:
                errors.append("check mode printed a hardcoded data repo name")
    finally:
        if saved_state is None:
            STATE.unlink(missing_ok=True)
        else:
            STATE.write_text(saved_state, encoding="utf-8")
        if saved_pointer is None:
            POINTER.unlink(missing_ok=True)
        else:
            POINTER.write_text(saved_pointer, encoding="utf-8")
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return errors


def _result(code: int, text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=code, stdout=text, stderr="" if code == 0 else text)
