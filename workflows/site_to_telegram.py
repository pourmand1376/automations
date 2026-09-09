#!/usr/bin/env python3
"""Publish new posts from an RSS/Atom feed to a Telegram channel."""
from __future__ import annotations

import html
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_FEED_URL = "https://amirpourmand.ir/index.xml"
DEFAULT_STATE_FILE = "state/amirpourmand_ir_to_telegram.json"
TELEGRAM_MESSAGE_LIMIT = 4096
log = logging.getLogger(__name__)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in element:
        if _local_name(child.tag) in wanted and child.text:
            return child.text.strip()
    return ""


def _link(element: ET.Element) -> str:
    for child in element:
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href and child.attrib.get("rel", "alternate") == "alternate":
            return href.strip()
        if child.text:
            return child.text.strip()
    return ""


def parse_feed(payload: bytes) -> list[dict[str, str]]:
    """Parse RSS 2.x or Atom entries into a common representation."""
    root = ET.fromstring(payload)
    entries = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    posts = []
    for entry in entries:
        link = _link(entry)
        post_id = _child_text(entry, "guid", "id") or link
        title = _child_text(entry, "title") or "Untitled post"
        summary = _child_text(entry, "description", "summary", "content")
        if post_id and link:
            posts.append({"id": post_id, "title": title, "link": link, "summary": summary})
    return posts


def _plain_text(value: str) -> str:
    value = html.unescape(value)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def format_message(post: dict[str, str]) -> str:
    message = f'<b>{html.escape(post["title"])}</b>\n{html.escape(post["link"])}'
    summary = _plain_text(post.get("summary", ""))
    if summary:
        remaining = TELEGRAM_MESSAGE_LIMIT - len(message) - 5
        if remaining > 20:
            message += "\n\n" + html.escape(summary[:remaining].rstrip())
    return message[:TELEGRAM_MESSAGE_LIMIT]


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "automations/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _send_telegram(token: str, channel: str, message: str) -> None:
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": channel,
        "text": message,
        "parse_mode": "HTML",
    }).encode()
    request = urllib.request.Request(endpoint, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram API returned HTTP {error.code}: {detail}") from error
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {"initialized": False, "posted_ids": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not channel:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set")

    feed_url = os.getenv("FEED_URL", DEFAULT_FEED_URL)
    state_path = Path(os.getenv("STATE_FILE", DEFAULT_STATE_FILE))
    posts = parse_feed(_fetch(feed_url))
    state = _read_state(state_path)
    known = set(state.get("posted_ids", []))

    if not state.get("initialized", False):
        log.info("Initializing state with %d existing feed entries", len(posts))
        _write_state(state_path, {
            "initialized": True,
            "posted_ids": [post["id"] for post in posts],
        })
        return

    new_posts = [post for post in reversed(posts) if post["id"] not in known]
    for post in new_posts:
        log.info("Publishing: %s", post["title"])
        _send_telegram(token, channel, format_message(post))
        known.add(post["id"])
        state["posted_ids"] = list(dict.fromkeys(
            [post["id"] for post in posts] + list(known)
        ))[:500]
        _write_state(state_path, state)

    state["initialized"] = True
    state["posted_ids"] = list(dict.fromkeys(
        [post["id"] for post in posts] + list(known)
    ))[:500]
    _write_state(state_path, state)
    log.info("Published %d new post(s)", len(new_posts))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        run()
    except (ET.ParseError, OSError, RuntimeError, urllib.error.URLError) as error:
        log.error("Workflow failed: %s", error)
        sys.exit(1)
