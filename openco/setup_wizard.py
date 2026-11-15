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
from openco.paths import ROOT, STATE, TEMPLATES

PLACEHOLDER_NAME = "company-data"
REQUIRED = ("prerequisites", "github-repo", "scaffold", "remote", "push", "ci")
OPTIONAL = ("apps-notes", "apps-voice", "apps-calls", "memory", "skills", "mcp")
STEPS = REQUIRED + OPTIONAL
FINISHED_APP = {"done", "agent", "link"}

# Install commands checked against https://formulae.brew.sh/api/cask/<token>.json
# on 2026-11-15. Obsidian lists darwin and linux. Wispr Flow and Granola list
# darwin only. Wispr's Linux variation is not in supported_platforms and is
# not used. Anything else gets the official download page.
VERIFIED_APPS = {
    "notes": {
        "name": "Obsidian",
        "cask": "obsidian",
        "systems": frozenset({"darwin", "linux"}),
        "link": "https://obsidian.md/download",
        "why": "Notes app for the second brain. The data repo opens as a vault.",
    },
    "voice": {
        "name": "Wispr Flow",
        "cask": "wispr-flow",
        "systems": frozenset({"darwin"}),
        "link": "https://wisprflow.ai/downloads",
        "why": "Voice notes. On macOS this is the Homebrew cask wispr-flow.",
    },
    "calls": {
        "name": "Granola",
        "cask": "granola",
        "systems": frozenset({"darwin"}),
        "link": "https://www.granola.ai/download",
        "why": "Call recorder. Your agent is the other choice and installs nothing.",
    },
}


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

    def system(self) -> str:
        return sys.platform

    def have_brew(self) -> bool:
        return shutil.which("brew") is not None

    def brew(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, text=True, capture_output=True)


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
    print("This company starts empty. Nothing is imported.")
    _offer_apps(state, yes, reader, commands)
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
    _print_todo(record)


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
        if ensure_todo(dest):
            print(f"Wrote {dest / 'TODO.md'}. Commit it in your data repo when you are ready.")
        write_pointer(dest)
        return
    print(f"Copy the template into {dest} and make the first local commit.")
    ensure_skeleton(dest, name)
    ensure_todo(dest)
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


def _offer_apps(state, yes, reader, commands: Runner) -> None:
    state.setdefault("steps", {})
    if yes:
        for step in ("apps-notes", "apps-voice", "apps-calls"):
            state["steps"].setdefault(step, "skipped")
        save_state(state)
        print("Skipped app installs. Re-run without --yes to choose Obsidian, Wispr Flow, and Granola or your agent.")
        return
    _step_install(state, "apps-notes", "notes", reader, commands)
    _step_install(state, "apps-voice", "voice", reader, commands)
    _step_calls_app(state, reader, commands)


def _step_install(state, step: str, app: str, reader, commands: Runner) -> None:
    if _app_finished(state, step):
        return
    spec = VERIFIED_APPS[app]
    print(f"Optional: {spec['name']}. {spec['why']}")
    if not _confirm(f"Install {spec['name']}?", False, reader):
        state["steps"][step] = "skipped"
        save_state(state)
        return
    _run_or_link(state, step, app, commands)


def _step_calls_app(state, reader, commands: Runner) -> None:
    if _app_finished(state, "apps-calls"):
        return
    spec = VERIFIED_APPS["calls"]
    print(f"Optional: {spec['name']}. {spec['why']}")
    choice = reader("Granola, your agent, or skip? [granola/agent/skip] ").strip().lower()
    if choice in {"a", "agent"}:
        state["steps"]["apps-calls"] = "agent"
        save_state(state)
        print("Using your agent. Drop transcripts in calls/.")
        return
    if choice not in {"g", "granola", "y", "yes"}:
        state["steps"]["apps-calls"] = "skipped"
        save_state(state)
        return
    _run_or_link(state, "apps-calls", "calls", commands)


def _app_finished(state, step: str) -> bool:
    status = state["steps"].get(step)
    if status in FINISHED_APP:
        print(f"{step}: {status}")
        return True
    return False


def install_argv(app: str, system: str, have_brew: bool) -> list[str] | None:
    spec = VERIFIED_APPS[app]
    if have_brew and system in spec["systems"]:
        return ["brew", "install", "--cask", spec["cask"]]
    return None


def _run_or_link(state, step: str, app: str, commands: Runner) -> None:
    spec = VERIFIED_APPS[app]
    argv = install_argv(app, commands.system(), commands.have_brew())
    if argv is None:
        print(f"No verified install command for this OS. Download {spec['name']}: {spec['link']}")
        state["steps"][step] = "link"
        save_state(state)
        return
    print("Running " + " ".join(argv))
    result = commands.brew(argv)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OpencoError(detail or "install failed")
    state["steps"][step] = "done"
    save_state(state)


def _print_todo(record: dict) -> None:
    path = record.get("path")
    if not path:
        print("todo: missing")
        return
    dest = Path(path)
    todo = dest / "TODO.md"
    if not todo.is_file():
        print("todo: missing")
        return
    print(f"todo: {todo}")
    lines = todo.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("- ["):
            continue
        print(line)
        if index + 1 < len(lines) and lines[index + 1].strip().startswith("Done:"):
            print(lines[index + 1].rstrip())
    script = dest / "scripts" / "check.py"
    if not script.is_file():
        return
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(dest), "--voice-progress"],
        text=True,
        capture_output=True,
    )
    progress = (result.stdout or "").strip()
    if progress:
        print(progress)


def ensure_todo(dest: Path) -> bool:
    target = dest / "TODO.md"
    if target.is_file():
        return False
    source = TEMPLATES / "TODO.md"
    if not source.is_file():
        raise OpencoError("templates/data/TODO.md is missing")
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return True


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
            if "brew" in joined:
                errors.append("setup --yes ran an installer")
            if "- [ ] 6. Voice" not in report or "50 best posts" not in report:
                errors.append("check mode did not read the voice TODO")
            if "voice.md: best posts 0/50 (1 example)" not in report:
                errors.append("check mode did not report voice progress")
            if "export-notion" not in (dest / "TODO.md").read_text(encoding="utf-8"):
                errors.append("TODO does not keep the importers off the main path")
        errors.extend(_apps_selfcheck())
        errors.extend(_empty_voice_selfcheck())
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


def _apps_selfcheck() -> list[str]:
    """Check install commands. No package manager is run."""

    errors: list[str] = []
    expected = {
        ("notes", "darwin", True): ["brew", "install", "--cask", "obsidian"],
        ("notes", "linux", True): ["brew", "install", "--cask", "obsidian"],
        ("voice", "darwin", True): ["brew", "install", "--cask", "wispr-flow"],
        ("calls", "darwin", True): ["brew", "install", "--cask", "granola"],
        ("notes", "linux", False): None,
        ("voice", "linux", True): None,
        ("calls", "linux", True): None,
        ("notes", "win32", True): None,
        ("calls", "darwin", False): None,
    }
    for (app, system, have_brew), argv in expected.items():
        got = install_argv(app, system, have_brew)
        if got != argv:
            errors.append(f"install command for {app} on {system} brew={have_brew} was {got}")
        if got and any(part in {"snap", "apt", "winget", "choco"} for part in got):
            errors.append(f"install command guessed a package manager: {got}")

    class Fake(Runner):
        def __init__(self, system: str, have_brew: bool) -> None:
            self.commands: list[list[str]] = []
            self._system = system
            self._brew = have_brew

        def system(self) -> str:
            return self._system

        def have_brew(self) -> bool:
            return self._brew

        def brew(self, args: list[str]) -> subprocess.CompletedProcess[str]:
            self.commands.append(list(args))
            return _result(0, "installed\n")

    from io import StringIO

    darwin = Fake("darwin", True)
    answers = iter(["y", "y", "agent"])
    buffer = StringIO()
    real_stdout = sys.stdout
    sys.stdout = buffer
    try:
        _offer_apps({}, False, lambda _prompt: next(answers), darwin)
    finally:
        sys.stdout = real_stdout
    if darwin.commands != [
        ["brew", "install", "--cask", "obsidian"],
        ["brew", "install", "--cask", "wispr-flow"],
    ]:
        errors.append(f"darwin opt-in installs were {darwin.commands}")
    linux = Fake("linux", True)
    answers = iter(["y", "y", "granola"])
    buffer = StringIO()
    sys.stdout = buffer
    try:
        _offer_apps({}, False, lambda _prompt: next(answers), linux)
    finally:
        sys.stdout = real_stdout
    text = buffer.getvalue()
    if linux.commands != [["brew", "install", "--cask", "obsidian"]]:
        errors.append(f"linux installs were {linux.commands}")
    if "https://wisprflow.ai/downloads" not in text or "https://www.granola.ai/download" not in text:
        errors.append("linux path did not print the official download links")
    if "wispr-flow" in " ".join(" ".join(command) for command in linux.commands):
        errors.append("linux path installed Wispr Flow")
    return errors


def _empty_voice_selfcheck() -> list[str]:
    """An empty voice file still passes the data check and reports 0/50 and 0/20."""

    import tempfile

    errors: list[str] = []
    empty = (
        "# Voice\n\n"
        "## Words you never use\n\n"
        "- em dash\n\n"
        "## Your 50 best posts\n\n"
        "## 20 posts you hate\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "data"
        shutil.copytree(TEMPLATES, dest)
        (dest / "voice.md").write_text(empty, encoding="utf-8")
        script = dest / "scripts" / "check.py"
        result = subprocess.run([sys.executable, str(script), "--root", str(dest)], text=True, capture_output=True)
        if result.returncode != 0:
            errors.append(result.stderr.strip() or "empty voice.md failed CI")
        if "best posts 0/50" not in result.stdout or "hated posts 0/20" not in result.stdout:
            errors.append(f"empty voice progress was {result.stdout!r}")
    return errors


def _result(code: int, text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=code, stdout=text, stderr="" if code == 0 else text)
