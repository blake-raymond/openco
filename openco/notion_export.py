"""Read a Notion database and write markdown under me/notion/.

Endpoints, from the public API reference (Notion-Version 2026-03-11):

- GET /v1/databases/{database_id}
  https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03
- POST /v1/data_sources/{data_source_id}/query
  https://developers.notion.com/reference/query-a-data-source
- GET /v1/blocks/{block_id}/children
  https://developers.notion.com/reference/get-block-children

The upgrade guide's query example is labeled PATCH and then calls POST.
The reference and its curl example are POST, so this client uses POST.
No other write endpoint is called.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from openco.config import configured_data_repo
from openco.errors import OpencoError
from openco.second_brain import load_env

API = "https://api.notion.com"
NOTION_VERSION = "2026-03-11"
PAGE_SIZE = 100
Transport = Callable[[str, str, dict | None], dict]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    data_arg = None
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--data-repo":
            index += 1
            if index >= len(args):
                raise OpencoError("--data-repo needs a path")
            data_arg = args[index]
        else:
            raise OpencoError(f"unknown argument {item}")
        index += 1
    data_repo = configured_data_repo(data_arg)
    if data_repo is None or not data_repo.is_dir():
        raise OpencoError("no private data repo. Run make setup or pass --data-repo.")
    load_env()
    token = os.environ.get("NOTION_TOKEN", "").strip()
    database = os.environ.get("NOTION_SECOND_BRAIN_DB", "").strip()
    if not token or not database:
        raise OpencoError(
            "Set NOTION_TOKEN and NOTION_SECOND_BRAIN_DB in a gitignored .env file. "
            "See docs/setup/notion-second-brain.md."
        )
    written = export_database(data_repo, database, transport=_transport(token))
    print(f"wrote {len(written)} page(s) under me/notion/")
    for relative in written:
        print(f"  {relative}")
    print("Notion was only read. Commit me/notion/ on a branch. Do not commit it to main.")
    return 0


def export_database(data_repo: Path, database_id: str, transport: Transport) -> list[str]:
    database = _call(transport, "GET", f"/v1/databases/{database_id}", None)
    sources = database.get("data_sources") or []
    if not sources:
        raise OpencoError("the database response did not include data_sources")
    pages: list[dict] = []
    for source in sources:
        source_id = source.get("id")
        if not source_id:
            continue
        pages.extend(_query_pages(transport, source_id))
    folder = data_repo / "me" / "notion"
    folder.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    used: set[str] = set()
    for page in pages:
        if page.get("object") != "page":
            continue
        page_id = str(page.get("id", ""))
        title = _title(page) or "untitled"
        body = _blocks_markdown(transport, page_id, depth=0)
        slug = _unique_slug(title, page_id, used)
        relative = f"me/notion/{slug}.md"
        text = (
            "---\n"
            f"notion_page: {page_id}\n"
            "source: notion\n"
            "---\n\n"
            f"# {title}\n\n"
            f"{body.rstrip()}\n"
        )
        (data_repo / relative).write_text(text, encoding="utf-8")
        written.append(relative)
    keep = {Path(item).name for item in written} | {"README.md"}
    for path in folder.glob("*.md"):
        if path.name in keep:
            continue
        header = path.read_text(encoding="utf-8")[:200]
        if "source: notion" in header:
            path.unlink()
    return written


def _query_pages(transport: Transport, data_source_id: str) -> list[dict]:
    pages: list[dict] = []
    cursor = None
    for _ in range(100):
        body: dict = {"page_size": PAGE_SIZE}
        if cursor:
            body["start_cursor"] = cursor
        payload = _call(transport, "POST", f"/v1/data_sources/{data_source_id}/query", body)
        pages.extend(payload.get("results") or [])
        if not payload.get("has_more"):
            break
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    return pages


def _blocks_markdown(transport: Transport, block_id: str, depth: int) -> str:
    if depth > 8:
        return ""
    lines: list[str] = []
    cursor = None
    for _ in range(100):
        query = {"page_size": str(PAGE_SIZE)}
        if cursor:
            query["start_cursor"] = cursor
        path = "/v1/blocks/" + block_id + "/children?" + urllib.parse.urlencode(query)
        payload = _call(transport, "GET", path, None)
        for block in payload.get("results") or []:
            lines.append(_render_block(transport, block, depth))
        if not payload.get("has_more"):
            break
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    return "\n".join(line for line in lines if line is not None)


def _render_block(transport: Transport, block: dict, depth: int) -> str:
    kind = str(block.get("type") or "")
    payload = block.get(kind) if isinstance(block.get(kind), dict) else {}
    text = _plain(payload.get("rich_text") or [])
    prefix = ""
    if kind == "heading_1":
        prefix = "# "
    elif kind == "heading_2":
        prefix = "## "
    elif kind == "heading_3":
        prefix = "### "
    elif kind == "bulleted_list_item":
        prefix = "- "
    elif kind == "numbered_list_item":
        prefix = "1. "
    elif kind == "to_do":
        prefix = "- [x] " if payload.get("checked") else "- [ ] "
    elif kind == "quote":
        prefix = "> "
    elif kind == "code":
        language = payload.get("language") or ""
        text = f"```{language}\n{text}\n```"
    elif kind == "divider":
        text = "---"
    elif kind != "paragraph" and not text:
        text = ""
    rendered = f"{prefix}{text}".rstrip()
    if block.get("has_children") and block.get("id"):
        nested = _blocks_markdown(transport, str(block["id"]), depth + 1)
        if nested:
            rendered = (rendered + "\n\n" + nested).strip()
    return rendered


def _title(page: dict) -> str:
    properties = page.get("properties") or {}
    if not isinstance(properties, dict):
        return ""
    for value in properties.values():
        if isinstance(value, dict) and value.get("type") == "title":
            return _plain(value.get("title") or []).strip()
    return ""


def _plain(rich: object) -> str:
    if not isinstance(rich, list):
        return ""
    parts = []
    for item in rich:
        if isinstance(item, dict):
            parts.append(str(item.get("plain_text") or ""))
    return "".join(parts)


def _unique_slug(title: str, page_id: str, used: set[str]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or "untitled"
    slug = slug[:60].strip("-") or "untitled"
    if slug in used:
        suffix = re.sub(r"[^a-f0-9]", "", page_id.lower())[-6:] or "page"
        slug = f"{slug}-{suffix}"
    used.add(slug)
    return slug


def _call(transport: Transport, method: str, path: str, body: dict | None) -> dict:
    if method not in {"GET", "POST"}:
        raise OpencoError("export-notion is read-only")
    if method == "POST" and not path.endswith("/query"):
        raise OpencoError("export-notion is read-only")
    if not path.startswith("/v1/"):
        raise OpencoError("export-notion refused an unexpected Notion path")
    return transport(method, path, body)


def _transport(token: str) -> Transport:
    def send(method: str, path: str, body: dict | None) -> dict:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(API + path, data=data, method=method)
        request.add_header("Authorization", "Bearer " + token)
        request.add_header("Notion-Version", NOTION_VERSION)
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            message = _error_message(detail) or f"Notion returned HTTP {exc.code}"
            raise OpencoError(message) from exc
    return send


def _error_message(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""
    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return ""
