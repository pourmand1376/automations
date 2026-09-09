"""Export Raindrop bookmarks for motamem.org as a JSON URL list."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RAINDROP_API_URL = "https://api.raindrop.io/rest/v1/raindrops/0"
DEFAULT_PREFIX = "https://motamem.org/"
DEFAULT_SEARCH = "motamem.org"
DEFAULT_OUTPUT = Path("data/motamem_urls.json")
PER_PAGE = 50


def fetch_page(
    access_token: str,
    page: int,
    per_page: int = PER_PAGE,
    search: str = DEFAULT_SEARCH,
) -> list[dict[str, Any]]:
    """Fetch one page of bookmarks from all non-trash Raindrop collections."""
    query = urlencode(
        {"page": page, "perpage": per_page, "sort": "-created", "search": search}
    )
    request = Request(
        f"{RAINDROP_API_URL}?{query}",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if not payload.get("result", False):
        raise RuntimeError(f"Raindrop API returned an unsuccessful result: {payload!r}")
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError("Raindrop API returned an invalid items list")
    return items


def motamem_urls(items: list[dict[str, Any]], prefix: str = DEFAULT_PREFIX) -> list[str]:
    """Return unique bookmark URLs matching prefix, preserving feed order."""
    urls: list[str] = []
    seen: set[str] = set()
    for item in items:
        link = item.get("link")
        if isinstance(link, str) and link.startswith(prefix) and link not in seen:
            seen.add(link)
            urls.append(link)
    return urls


def write_urls(urls: list[str], output: Path = DEFAULT_OUTPUT) -> None:
    """Atomically write a stable, human-readable JSON array."""
    output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(urls, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as tmp:
        tmp.write(content)
        temporary_path = Path(tmp.name)
    temporary_path.replace(output)


def sync() -> int:
    token = os.environ.get("RAINDROP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("RAINDROP_ACCESS_TOKEN is required")

    prefix = os.environ.get("RAINDROP_URL_PREFIX", DEFAULT_PREFIX)
    search = os.environ.get("RAINDROP_SEARCH", DEFAULT_SEARCH)
    output = Path(os.environ.get("RAINDROP_OUTPUT_PATH", str(DEFAULT_OUTPUT)))
    all_items: list[dict[str, Any]] = []
    page = 0
    while True:
        items = fetch_page(token, page, search=search)
        all_items.extend(items)
        if len(items) < PER_PAGE:
            break
        page += 1

    urls = motamem_urls(all_items, prefix)
    write_urls(urls, output)
    print(f"Wrote {len(urls)} matching Raindrop URLs to {output}")
    return len(urls)


if __name__ == "__main__":
    sync()
