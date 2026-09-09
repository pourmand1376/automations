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
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

TELEGRAM_MESSAGE_LIMIT = 4096
log = logging.getLogger(__name__)

SITE_CONFIG = {
    "amirpourmand-ir": {
        "feed_url": "https://amirpourmand.ir/index.xml",
        "state_file": "state/amirpourmand_ir_to_telegram.json",
        "token_env": "TELEGRAM_BOT_TOKEN",
        "channel_env": "WEBSITES_TELEGRAM_CHANNEL_ID",
    },
    "aprd-ir": {
        "feed_url": "https://aprd.ir/index.xml",
        "state_file": "state/aprd_ir_to_telegram.json",
        "token_env": "TELEGRAM_BOT_TOKEN",
        "channel_env": "WEBSITES_TELEGRAM_CHANNEL_ID",
    },
    "castbox": {
        "feed_url": "http://rss.castbox.fm/everest/480c97a079254a06ba396783a44f0acc.xml",
        "state_file": "state/castbox_to_telegram.json",
        "token_env": "TELEGRAM_BOT_TOKEN",
        "channel_env": "CASTBOX_TELEGRAM_CHANNEL_ID",
    },
}


def _telegram_endpoint(token: str, method: str) -> str:
    base_url = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org").rstrip("/")
    return f"{base_url}/bot{token}/{method}"


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


def _audio(element: ET.Element) -> tuple[str, str]:
    for child in element:
        local_name = _local_name(child.tag)
        if local_name == "enclosure" or (local_name == "content" and child.attrib.get("medium") == "audio"):
            url = child.attrib.get("url")
            if url:
                return url.strip(), child.attrib.get("type", "")
        if local_name == "link" and child.attrib.get("rel") == "enclosure":
            href = child.attrib.get("href")
            if href:
                return href.strip(), child.attrib.get("type", "")
    return "", ""


def parse_feed(payload: bytes) -> list[dict[str, str]]:
    """Parse RSS 2.x or Atom entries into a common representation."""
    root = ET.fromstring(payload)
    entries = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    posts = []
    for entry in entries:
        link = _link(entry)
        audio_url, audio_type = _audio(entry)
        link = link or audio_url
        post_id = _child_text(entry, "guid", "id") or link
        title = _child_text(entry, "title") or "Untitled post"
        summary = _child_text(entry, "description", "summary", "content")
        if post_id and link:
            posts.append({
                "id": post_id,
                "title": title,
                "link": link,
                "summary": summary,
                "audio_url": audio_url,
                "audio_type": audio_type,
            })
    return posts


class _DescriptionParser(HTMLParser):
    """Convert feed HTML into Telegram HTML while preserving its structure."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n\n<b>")
        elif tag == "p":
            self.parts.append("\n\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.parts.append(f'<a href="{html.escape(href, quote=True)}">')

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("</b>\n")
        elif tag == "p":
            self.parts.append("\n")
        elif tag == "a":
            self.parts.append("</a>")

    def handle_data(self, data: str) -> None:
        self.parts.append(html.escape(re.sub(r"[ \t\f\v]+", " ", data)))

    def result(self) -> str:
        value = "".join(self.parts)
        value = re.sub(r" *\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def _format_description(value: str) -> str:
    parser = _DescriptionParser()
    parser.feed(value)
    parser.close()
    return parser.result()


def format_message(post: dict[str, str]) -> str:
    message = f'<b>{html.escape(post["title"])}</b>\n{html.escape(post["link"])}'
    summary = _format_description(post.get("summary", ""))
    if summary:
        remaining = TELEGRAM_MESSAGE_LIMIT - len(message) - 5
        if remaining > 20:
            message += "\n\n" + summary[:remaining].rstrip()
    return message[:TELEGRAM_MESSAGE_LIMIT]


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "automations/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _send_telegram(token: str, channel: str, message: str) -> None:
    endpoint = _telegram_endpoint(token, "sendMessage")
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


def _send_telegram_media(token: str, channel: str, post: dict[str, str]) -> None:
    """Download and upload an RSS enclosure, preserving unsupported audio types as documents."""
    request = urllib.request.Request(post["audio_url"], headers={"User-Agent": "automations/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read(50 * 1024 * 1024 + 1)
        content_type = response.headers.get_content_type()
    if len(data) > 50 * 1024 * 1024:
        raise RuntimeError("Audio file is larger than Telegram's 50 MB bot upload limit")

    parsed_url = urllib.parse.urlsplit(post["audio_url"])
    filename = Path(urllib.parse.unquote(parsed_url.path)).name or "episode.audio"
    audio_type = post.get("audio_type") or content_type
    method = "sendAudio" if audio_type in {"audio/mpeg", "audio/mp3", "audio/mp4", "audio/x-m4a"} or filename.lower().endswith((".mp3", ".m4a")) else "sendDocument"
    field = "audio" if method == "sendAudio" else "document"
    caption = f'<b>{html.escape(post["title"])}</b>\n{html.escape(post["link"])}'
    boundary = f"----automations-{uuid4().hex}"
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{channel}\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\nContent-Type: {audio_type or 'application/octet-stream'}\r\n\r\n".encode(),
        data,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    request = urllib.request.Request(
        _telegram_endpoint(token, method),
        data=b"".join(chunks),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram media API returned HTTP {error.code}: {detail}") from error
    if not result.get("ok"):
        raise RuntimeError(f"Telegram media API error: {result}")


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {"initialized": False, "posted_ids": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(site: str) -> None:
    if site not in SITE_CONFIG:
        raise RuntimeError(f"Unknown site: {site}")
    config = SITE_CONFIG[site]
    token = os.getenv(config["token_env"])
    channel = os.getenv(config["channel_env"])
    if not token or not channel:
        raise RuntimeError(f'{config["token_env"]} and {config["channel_env"]} must be set')

    feed_url = config["feed_url"]
    state_path = Path(config["state_file"])
    posts = parse_feed(_fetch(feed_url))
    state = _read_state(state_path)
    known = set(state.get("posted_ids", []))

    # An empty initialized state can be left by an older parser that did not
    # understand this feed. Rebuild it as a baseline without reposting the archive.
    if not state.get("initialized", False) or not state.get("posted_ids"):
        log.info("Initializing state with %d existing feed entries", len(posts))
        _write_state(state_path, {
            "initialized": True,
            "posted_ids": [post["id"] for post in posts],
        })
        return

    new_posts = [post for post in reversed(posts) if post["id"] not in known]
    for post in new_posts:
        log.info("Publishing: %s", post["title"])
        if post.get("audio_url"):
            _send_telegram_media(token, channel, post)
        else:
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
        run("amirpourmand-ir")
    except (ET.ParseError, OSError, RuntimeError, urllib.error.URLError) as error:
        log.error("Workflow failed: %s", error)
        sys.exit(1)
