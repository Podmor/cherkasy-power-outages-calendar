"""Turn parsed daily schedules into calendar events and keep the state between runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

KEEP_DAYS = 30


@dataclass(frozen=True)
class Interval:
    start: datetime  # UTC, aware
    end: datetime  # UTC, aware

    @property
    def uid_key(self) -> str:
        return self.start.strftime("%Y%m%dT%H%M")


def load_state(path: Path, queue: str) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"queue": queue, "days": {}, "events": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def prune_days(state: dict, today: date) -> None:
    limit = today - timedelta(days=KEEP_DAYS)
    for key in list(state["days"]):
        if date.fromisoformat(key) < limit:
            del state["days"][key]


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


def sync_language(state: dict, language: str, now: datetime) -> bool:
    """When the calendar language changes, mark every event as modified.

    Calendar apps only re-read an event when its SEQUENCE / LAST-MODIFIED grows, so without
    this the old texts could stay on the phone. State files written before this field existed
    were always generated in Russian.
    """
    previous = state.get("language", "ru" if state.get("events") else language)
    state["language"] = language
    if previous == language:
        return False
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    for ev in state.get("events", {}).values():
        ev["seq"] += 1
        ev["modified"] = stamp
    return True


def local_runs(intervals: list[Interval], tz: ZoneInfo) -> tuple[set[datetime], set[datetime]]:
    """Naive local start and end times of all intervals (used for sanity checks)."""
    starts = {iv.start.astimezone(tz).replace(tzinfo=None) for iv in intervals}
    ends = {iv.end.astimezone(tz).replace(tzinfo=None) for iv in intervals}
    return starts, ends
