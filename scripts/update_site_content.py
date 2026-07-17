#!/usr/bin/env python3
"""Update protected README sections from the public xiaodudu.top APIs."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SITE = "https://www.xiaodudu.top"
LIMIT = 5


def fetch_items(resource: str) -> list[dict]:
    request = urllib.request.Request(
        f"{SITE}/api/{resource}",
        headers={"Accept": "application/json", "User-Agent": "promotesd-profile-readme"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except Exception as error:
        print(f"Could not fetch {resource}: {error}")
        return []

    items = payload.get("data", payload) if isinstance(payload, dict) else payload
    return items if isinstance(items, list) else []


def plain_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^]]*]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#~-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def escape_markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def item_date(item: dict) -> str:
    value = item.get("published_at") or item.get("date") or item.get("created_at") or item.get("updated_at") or ""
    return str(value)[:10]


def render(items: list[dict], resource: str) -> str:
    if not items:
        label = "blog posts" if resource == "blogs" else "diary entries"
        return f"_No published {label} yet._"

    rows = []
    for item in items[:LIMIT]:
        title = escape_markdown(plain_text(item.get("title") or "Untitled"))
        slug = item.get("slug") or item.get("id")
        path = f"/blogs/{slug}" if resource == "blogs" and slug else "/diary"
        summary = plain_text(item.get("excerpt") or item.get("summary") or item.get("description") or item.get("content"))
        summary = escape_markdown(summary[:120] + ("..." if len(summary) > 120 else ""))
        date = item_date(item)
        suffix = f" · {date}" if date else ""
        rows.append(f"- **[{title}]({SITE}{path})**{suffix}" + (f"  \n  {summary}" if summary else ""))
    return "\n".join(rows)


def replace_section(content: str, marker: str, rendered: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{rendered}\n{end}"
    if not pattern.search(content):
        raise RuntimeError(f"README marker is missing: {marker}")
    return pattern.sub(lambda _: replacement, content)


def main() -> None:
    content = README.read_text(encoding="utf-8")
    content = replace_section(content, "XIAODUDU_BLOG", render(fetch_items("blogs"), "blogs"))
    content = replace_section(content, "XIAODUDU_DIARY", render(fetch_items("diaries"), "diaries"))
    README.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
