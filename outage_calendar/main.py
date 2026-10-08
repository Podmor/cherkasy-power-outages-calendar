"""Entry point: read the channels, update the schedules, write the .ics files."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from PIL import Image

from .ics import build_ics
from .schedule import (
    build_intervals,
    load_state,
    local_runs,
    prune_days,
    save_state,
    sync_events,
)
from .telegram import Post, fetch_posts, http_get, parse_caption_date, parse_notice
from .wheel import WheelError, parse_wheel


def photo_key(url: str) -> str:
    return hashlib.sha1(urlparse(url).path.encode()).hexdigest()[:12]


def update_days(state: dict, posts: list[Post], tz: ZoneInfo, fetch_bytes, log) -> list[str]:
    """Read new schedule images. Returns a list of problems (empty when all is fine)."""
    problems: list[str] = []
    for post in posts:  # oldest first, so a later post for the same day wins
        if not post.photo_url:
            continue
        day = parse_caption_date(post.text, post.posted_at, tz)
        if day is None:
            log(f"post {post.id}: photo without a date in the caption, skipped")
            continue
        key = day.isoformat()
        known = state["days"].get(key)
        pkey = photo_key(post.photo_url)
        if known and (known["post"] > post.id or (known["post"] == post.id and known["photo"] == pkey)):
            continue
        try:
            image = Image.open(io.BytesIO(fetch_bytes(post.photo_url)))
            hours = parse_wheel(image)
        except (WheelError, OSError) as exc:
            msg = f"post {post.id} ({key}): cannot read the image: {exc}"
            log(msg)
            problems.append(msg)
            continue
        state["days"][key] = {
            "hours": hours,
            "post": post.id,
            "photo": pkey,
            "posted_at": post.posted_at.isoformat(),
        }
        log(f"post {post.id}: {key} -> outage hours {hours}")
    return problems


def crosscheck(posts: list[Post], intervals, days: dict, tz: ZoneInfo, log) -> list[str]:
    """Compare the bot's text notices ('power on at 09:00') with what we read from images.

    Only notices posted after the day's latest schedule image are compared; older ones
    describe an earlier version of the schedule. Returns the list of warnings.
    """
    warnings: list[str] = []
    starts, ends = local_runs(intervals, tz)
    newest = max((p.posted_at for p in posts), default=None)
    if newest is None:
        return warnings
    for post in posts:
        if (newest - post.posted_at).total_seconds() > 24 * 3600:
            continue
        notice = parse_notice(post.text, post.posted_at, tz)
        if notice is None:
            continue
        kind, when = notice
        info = days.get(when.date().isoformat())
        if info is None or post.posted_at < datetime.fromisoformat(info["posted_at"]):
            continue
        ok = when in (ends if kind == "on" else starts)
        if not ok:
            msg = f"notice in post {post.id} ('{post.text}') does not match the schedule read from images"
            log(f"warning: {msg}")
            warnings.append(msg)
    return warnings


def run_queue(root: Path, cfg: dict, qcfg: dict, fetch_html, fetch_bytes, now: datetime, log) -> int:
    tz = ZoneInfo(cfg.get("timezone", "Europe/Kyiv"))
    queue, channel = qcfg["queue"], qcfg["channel"]
    state_path = root / "state" / f"{queue}.json"
    ics_path = root / "docs" / f"{queue}.ics"

    state = load_state(state_path, queue)
    posts = fetch_posts(channel, pages=cfg.get("pages", 2), fetch=fetch_html)
    log(f"[{queue}] read {len(posts)} posts from @{channel}")

    problems = update_days(state, posts, tz, fetch_bytes, log)
    prune_days(state, now.astimezone(tz).date())

    intervals = build_intervals(state["days"], tz)
    sync_events(state, intervals, now)
    crosscheck(posts, intervals, state["days"], tz, log)

    ics_text = build_ics(queue, channel, state["events"], cfg.get("language", "ru"), cfg.get("alarm_minutes", [15]))
    ics_path.parent.mkdir(parents=True, exist_ok=True)
    ics_path.write_bytes(ics_text.encode("utf-8"))
    save_state(state_path, state)
    log(f"[{queue}] {len(state['events'])} events in {ics_path.name}")

    # If the newest schedule image cannot be read, fail the run so GitHub emails the owner.
    newest_photo = max((p for p in posts if p.photo_url), key=lambda p: p.id, default=None)
    if problems and newest_photo and any(f"post {newest_photo.id} " in m for m in problems):
        return 1
    return 0


def run(root: Path, fetch_html=http_get, fetch_bytes=http_get, now: datetime | None = None, log=print) -> int:
    cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
    now = now or datetime.now(timezone.utc)
    code = 0
    for qcfg in cfg["queues"]:
        code = max(code, run_queue(root, cfg, qcfg, fetch_html, fetch_bytes, now, log))
    return code


def main() -> None:
    sys.exit(run(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    main()
