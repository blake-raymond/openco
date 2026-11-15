"""Secret and contact-detail checks for text that would be committed.

Example-domain addresses are allowed so docs can talk about the rule.
The patterns live here as expressions; the self-check builds sample
values at runtime so this file does not contain a real-looking secret.
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


def scan_text(path: str, text: str) -> list[str]:
    findings: list[str] = []
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
