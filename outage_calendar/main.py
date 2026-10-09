"""Entry point: read the official channel, update the schedules, write the .ics files."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .ics import build_ics, text_fingerprint
from .index_page import build_index
from .official import GpvPost, OfficialParseError, is_gpv, parse_gpv
from .schedule import (
    apply_post,
    build_intervals,
    load_state,
    prune_days,
    save_state,
    sync_events,
    sync_texts,
)
from .telegram import fetch_posts, http_get


def read_schedule_posts(posts, tz: ZoneInfo, log) -> tuple[list[GpvPost], list[str], int | None]:
    """Parse every schedule post. Returns (posts, problems, id of the newest schedule post)."""
    parsed: list[GpvPost] = []
    problems: list[str] = []
    newest: int | None = None
    for post in posts:  # oldest first
        if not is_gpv(post.text):
            continue
        newest = post.id
        try:
            parsed.append(parse_gpv(post.id, post.posted_at, post.text, tz))
        except OfficialParseError as exc:
            msg = f"post {post.id}: cannot read the schedule: {exc}"
            log(msg)
            problems.append(msg)
    return parsed, problems, newest


def run_queue(root: Path, cfg: dict, queue: str, schedule_posts: list[GpvPost], now: datetime, log) -> None:
    tz = ZoneInfo(cfg.get("timezone", "Europe/Kyiv"))
    channel = cfg["channel"]
    alarms = cfg.get("alarm_minutes", [15])
    state_path = root / "state" / f"{queue}.json"
    ics_path = root / "docs" / f"{queue}.ics"

    state = load_state(state_path, queue)
    for p in schedule_posts:
        # A queue that is not listed in a post has no outages in the part of the day it covers.
        if apply_post(state, p.day, p.queues.get(queue, []), p.post_id, p.posted_at, tz):
            log(f"[{queue}] post {p.post_id}: {p.day} -> outage hours {state['days'][p.day]['hours']}")
    prune_days(state, now.astimezone(tz).date())

    intervals = build_intervals(state["days"], tz)
    if sync_texts(state, text_fingerprint(queue, channel, alarms), now):
        log(f"[{queue}] texts changed, all events marked as modified")
    sync_events(state, intervals, now)

    ics_path.parent.mkdir(parents=True, exist_ok=True)
    ics_path.write_bytes(build_ics(queue, channel, state["events"], alarms).encode("utf-8"))
    save_state(state_path, state)
    log(f"[{queue}] {len(state['events'])} events in {ics_path.name}")


def run(root: Path, fetch_html=http_get, now: datetime | None = None, log=print) -> int:
    cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
    tz = ZoneInfo(cfg.get("timezone", "Europe/Kyiv"))
    now = now or datetime.now(timezone.utc)

    posts = fetch_posts(cfg["channel"], pages=cfg.get("pages", 4), fetch=fetch_html)
    log(f"read {len(posts)} posts from @{cfg['channel']}")
    schedule_posts, problems, newest = read_schedule_posts(posts, tz, log)

    for queue in cfg["queues"]:
        run_queue(root, cfg, queue, schedule_posts, now, log)

    index = root / "docs" / "index.html"
    index.write_text(build_index(cfg["site_url"], cfg["queues"], cfg["channel"]), encoding="utf-8")

    # If the newest schedule post cannot be read, fail the run so GitHub emails the owner.
    if newest is not None and any(f"post {newest}:" in m for m in problems):
        return 1
    return 0


def main() -> None:
    sys.exit(run(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    main()
