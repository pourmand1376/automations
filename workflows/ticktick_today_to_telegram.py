#!/usr/bin/env python3
"""Send changed TickTick Today-style tasks to a Telegram channel."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from workflows.site_to_telegram import _send_telegram

TODAY_STATE_FILE = "state/ticktick_today_alerts.json"
TEHRAN = ZoneInfo("Asia/Tehran")
log = logging.getLogger(__name__)


def _task_date(value: object) -> date | None:
    if not value:
        return None
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo:
        parsed = parsed.astimezone(TEHRAN)
    return parsed.date()


def get_today_tasks(token: str) -> list[dict]:
    """Fetch open tasks through the CLI and derive a Today-style list locally."""
    subprocess.run(["ticktick", "auth", "token", token], check=True, capture_output=True, text=True)
    result = subprocess.run(
        ["ticktick", "task", "filter", "--status", "0", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    today = date.today()
    tasks = json.loads(result.stdout)
    selected = []
    for task in tasks:
        dates = [_task_date(task.get("startDate")), _task_date(task.get("dueDate"))]
        if any(task_date and task_date <= today for task_date in dates):
            selected.append(task)
    return selected


def _message(tasks: list[dict]) -> str:
    lines = ["<b>TickTick Today</b>", ""]
    for task in tasks:
        title = str(task.get("title", "(untitled)")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"• {title}")
    return "\n".join(lines)


def run() -> None:
    token = os.getenv("TICKTICK_ACCESS_TOKEN")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("PERSONAN_CHAT_ID_TELEGRAM")
    if not token or not telegram_token or not channel:
        raise RuntimeError("TICKTICK_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, and PERSONAN_CHAT_ID_TELEGRAM must be set")

    state_path = Path(os.getenv("TICKTICK_TODAY_STATE_FILE", TODAY_STATE_FILE))
    tasks = get_today_tasks(token)
    current = {
        "date": date.today().isoformat(),
        "task_ids": sorted(str(task["id"]) for task in tasks),
    }
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if previous == current:
        log.info("Today task list has not changed; no alert sent")
        return

    _send_telegram(telegram_token, channel, _message(tasks) if tasks else "<b>TickTick Today</b>\n\nNo open tasks.")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log.info("Sent Today alert for %d task(s)", len(tasks))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()
