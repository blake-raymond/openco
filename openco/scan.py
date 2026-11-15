"""Secret, contact-detail, and transcript checks for the public repo.

Example-domain addresses are allowed so docs can talk about the rule.
The patterns live here as expressions; the self-check builds sample
values at runtime so this file does not contain a real-looking secret.

Transcripts belong in the private data repo. A markdown file under
calls/, or a file whose own front matter says it is a transcript, is
rejected here. Docs may describe the format without being that file.
"""

import re

_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("cloud access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github fine-grained token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("api token", re.compile(r"(?:sk|xai)-[A-Za-z0-9]{20,}")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\b\d{3}-\d{3}-\d{4}\b")),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
    ),
]

_EMAIL_OK = {"example.com", "example.org", "example.net"}


def transcript_finding(relative: str, text: str) -> str | None:
    """Return an error if this public-repo path is a transcript."""

    rel = relative.replace("\\", "/")
    name = rel.rsplit("/", 1)[-1]
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    if (parent == "calls" or parent.endswith("/calls")) and name.endswith(".md") and name != "README.md":
        return f"{relative}: transcripts belong in the private data repo, not openco"
    if rel.startswith("docs/"):
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    front = text[4:end]
    if re.search(r"(?m)^kind:\s*(transcript|meeting)\s*$", front):
        return f"{relative}: transcripts belong in the private data repo, not openco"
    if re.search(r"(?m)^source:\s*(generic-transcript|granola)\s*$", front):
        return f"{relative}: transcripts belong in the private data repo, not openco"
    return None


def scan_text(path: str, text: str) -> list[str]:
    findings: list[str] = []
    transcript = transcript_finding(path, text)
    if transcript:
        findings.append(transcript)
    for name, pattern in _RULES:
        for match in pattern.finditer(text):
            if name == "email" and match.group(1).lower() in _EMAIL_OK:
                continue
            findings.append(f"{path}: possible {name}")
            break
    return findings


def scan_file(path) -> list[str]:
    file_path = path
    if file_path.stat().st_size > 1_000_000:
        return [f"{file_path}: file is over 1MB"]
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{file_path}: file is not UTF-8 text"]
    return scan_text(str(file_path), text)
