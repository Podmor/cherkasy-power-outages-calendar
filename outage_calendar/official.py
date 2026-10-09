"""Read the schedule posts of the official channel of Cherkasyoblenergo.

A post looks like this (text only, no picture)::

    Оновлений графік погодинних відключень (ГПВ) на 8 жовтня.
    Години відсутності електропостачання:
    1.1 11:00 - 13:00, 17:00 - 19:00
    1.2 07:00 - 09:00, ...
    ...
    6.2 ...

A post that is published during the day lists only the hours that are still ahead
(the outage that is running right now is listed whole). Merging such partial posts into
a full day is done in schedule.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .telegram import parse_caption_date

MARKER = "Години відсутності електропостачання"

# A queue label ("3.1") followed by its time ranges.
_LABEL_RE = re.compile(r"(?<![\d.:])([1-9]\.[12])(?=\s+\d{1,2}:\d{2})")
_RANGES_RE = re.compile(r"\s*((?:\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*,?\s*)+)")
_RANGE_RE = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")


class OfficialParseError(Exception):
    """The post looks like a schedule but cannot be read."""


@dataclass
class GpvPost:
    post_id: int
    posted_at: datetime  # UTC
    day: str  # ISO date the schedule is about
    queues: dict[str, list[int]]  # queue label -> hours without power (queues absent from the post have none)


def is_gpv(text: str) -> bool:
    return MARKER in text


def _hours(ranges_text: str) -> list[int]:
    hours: set[int] = set()
    for m in _RANGE_RE.finditer(ranges_text):
        a_h, a_m, b_h, b_m = (int(x) for x in m.groups())
        if a_m or b_m:
            raise OfficialParseError(f"time not on a whole hour: {m.group(0)}")
        if b_h == 0:
            b_h = 24
        if not (0 <= a_h < b_h <= 24):
            raise OfficialParseError(f"bad time range: {m.group(0)}")
        hours.update(range(a_h, b_h))
    return sorted(hours)


def parse_gpv(post_id: int, posted_at: datetime, text: str, tz: ZoneInfo) -> GpvPost:
    head, _, body = text.partition(MARKER)
    day = parse_caption_date(head, posted_at, tz)
    if day is None:
        raise OfficialParseError("no date in the post header")
    labels = list(_LABEL_RE.finditer(body))
    if not labels:
        raise OfficialParseError("no queues in the post")
    queues: dict[str, list[int]] = {}
    for i, m in enumerate(labels):
        end = labels[i + 1].start() if i + 1 < len(labels) else len(body)
        chunk = body[m.end():end]
        r = _RANGES_RE.match(chunk)
        if r is None:
            raise OfficialParseError(f"queue {m.group(1)}: no time ranges")
        rest = chunk[r.end():]
        # Anything left before the next label must not look like another (unreadable) time.
        if i + 1 < len(labels) and re.search(r"\d{1,2}:\d{2}", rest):
            raise OfficialParseError(f"queue {m.group(1)}: unreadable text '{rest.strip()[:40]}'")
        if m.group(1) in queues:
            raise OfficialParseError(f"queue {m.group(1)} appears twice")
        queues[m.group(1)] = _hours(r.group(1))
    return GpvPost(post_id, posted_at, day.isoformat(), queues)
