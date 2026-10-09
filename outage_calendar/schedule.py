"""Turn parsed daily schedules into calendar events and keep the state between runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

KEEP_DAYS = 30

# Bump when the way "days" are read from the channel changes: old days are then dropped
# and read again from the posts, while the events (with their SEQUENCE numbers) are kept.
SOURCE = "pat_cherkasyoblenergo/text-v1"


@dataclass(frozen=True)
class Interval:
    start: datetime  # UTC, aware
    end: datetime  # UTC, aware

    @property
    def uid_key(self) -> str:
        return self.start.strftime("%Y%m%dT%H%M")


def load_state(path: Path, queue: str) -> dict:
    state = {"queue": queue, "source": SOURCE, "days": {}, "events": {}, "fingerprint": None}
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        state["events"] = old.get("events", {})
        state["fingerprint"] = old.get("fingerprint")
        if old.get("source") == SOURCE:
            state["days"] = old.get("days", {})
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def prune_days(state: dict, today: date) -> None:
    limit = today - timedelta(days=KEEP_DAYS)
    for key in list(state["days"]):
        if date.fromisoformat(key) < limit:
            del state["days"][key]


def apply_post(state: dict, day: str, hours: list[int], post_id: int, posted_at: datetime, tz: ZoneInfo) -> bool:
    """Merge one schedule post into state['days'][day]. Returns True when it was applied.

    A post published during the day lists only the hours that are still ahead (the outage
    running at that moment is listed whole), so everything before the first listed hour
    or before the current hour - whichever is earlier - is kept from the earlier posts.
    A post published before the day starts replaces the whole day.
    """
    known = state["days"].get(day)
    if known and known["post"] >= post_id:
        return False
    d = date.fromisoformat(day)
    day_start = datetime(d.year, d.month, d.day, tzinfo=tz)
    elapsed = int((posted_at - day_start).total_seconds() // 3600)
    elapsed = max(0, min(24, elapsed))
    cut = min(elapsed, min(hours)) if hours else elapsed
    kept = [h for h in (known["hours"] if known else []) if h < cut]
    state["days"][day] = {
        "hours": sorted(set(kept) | set(hours)),
        "post": post_id,
        "posted_at": posted_at.isoformat(),
    }
    return True


def build_intervals(days: dict, tz: ZoneInfo) -> list[Interval]:
    """Group consecutive outage hours (also across midnight) into intervals."""
    starts: list[datetime] = []
    for key, info in days.items():
        d = date.fromisoformat(key)
        for hour in info["hours"]:
            local = datetime(d.year, d.month, d.day, tzinfo=tz) + timedelta(hours=hour)
            starts.append(local.astimezone(timezone.utc))
    starts = sorted(set(starts))
    intervals: list[Interval] = []
    for s in starts:
        e = s + timedelta(hours=1)
        if intervals and intervals[-1].end == s:
            intervals[-1] = Interval(intervals[-1].start, e)
        else:
            intervals.append(Interval(s, e))
    return intervals


def sync_texts(state: dict, fingerprint: str, now: datetime) -> bool:
    """When the texts of the calendar change, mark every event as modified.

    Calendar apps only re-read an event when its SEQUENCE / LAST-MODIFIED grows, so without
    this the old texts could stay on the phone. A queue that has no events yet (first run)
    has nothing to mark.
    """
    previous = state.get("fingerprint")
    state["fingerprint"] = fingerprint
    if previous == fingerprint or (previous is None and not state["events"]):
        return False
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    for ev in state["events"].values():
        ev["seq"] += 1
        ev["modified"] = stamp
    return True


def sync_events(state: dict, intervals: list[Interval], now: datetime) -> bool:
    """Update state['events'] to match intervals. Returns True when anything changed."""
    old = state.get("events", {})
    new: dict[str, dict] = {}
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    for iv in intervals:
        key = iv.uid_key
        end = iv.end.strftime("%Y%m%dT%H%M%SZ")
        prev = old.get(key)
        if prev is None:
            new[key] = {"end": end, "seq": 0, "modified": stamp}
        elif prev["end"] != end:
            new[key] = {"end": end, "seq": prev["seq"] + 1, "modified": stamp}
        else:
            new[key] = prev
    changed = new != old
    state["events"] = new
    return changed
