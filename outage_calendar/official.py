"""Read the schedule posts of the official channel of Cherkasyoblenergo.

A post looks like this (text only, no picture)::

    Оновлений графік погодинних відключень (ГПВ) на 8 жовтня.
    Години відсутності електропостачання:
    1.1 11:00 - 13:00, 17:00 - 19:00
    1.2 07:00 - 09:00, ...
    ...
    6.2 ...

Outage times are not always whole hours (for example "16:30 - 19:00"), so a day is kept as
a list of (start, end) pairs in minutes since local midnight, end exclusive. Times must be
a multiple of 5 minutes. A post that is published during the day lists only the outages
that are still ahead (the outage that is running right now is listed whole). Merging such
partial posts into a full day is done in schedule.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .telegram import parse_caption_date

MARKER = "Години відсутності електропостачання"

# A queue label ("3.1") followed by its time ranges. The channel sometimes has typos:
# a dot after the label ("5.2. 17:00 - 19:00") or a longer dash between the times.
_DASH = "[-\u2010-\u2015\u2212]"  # hyphen, en dash, em dash, minus sign, ...
_LABEL_RE = re.compile(r"(?<![\d.:])([1-9]\.[12])\.?(?=\s+\d{1,2}:\d{2})")
_RANGES_RE = re.compile(rf"\s*((?:\d{{1,2}}:\d{{2}}\s*{_DASH}\s*\d{{1,2}}:\d{{2}}\s*,?\s*)+)")
_RANGE_RE = re.compile(rf"(\d{{1,2}}):(\d{{2}})\s*{_DASH}\s*(\d{{1,2}}):(\d{{2}})")


class OfficialParseError(Exception):
    """The post looks like a schedule but cannot be read."""


@dataclass
class GpvPost:
    post_id: int
    posted_at: datetime  # UTC
    day: str  # ISO date the schedule is about
    # queue label -> (start, end) minutes since local midnight without power
    # (queues absent from the post have none)
    queues: dict[str, list[tuple[int, int]]]


def is_gpv(text: str) -> bool:
    return MARKER in text


def merge_ranges(ranges) -> list[tuple[int, int]]:
    """Sort ranges and join the ones that touch or overlap."""
    out: list[list[int]] = []
    for a, b in sorted((int(a), int(b)) for a, b in ranges if b > a):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _ranges(ranges_text: str) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    for m in _RANGE_RE.finditer(ranges_text):
        a_h, a_m, b_h, b_m = (int(x) for x in m.groups())
        start, end = a_h * 60 + a_m, b_h * 60 + b_m
        if end == 0:  # "... - 00:00" means the end of the day
            end = 24 * 60
        if a_m >= 60 or b_m >= 60 or start % 5 or end % 5 or not (0 <= start < end <= 24 * 60):
            raise OfficialParseError(f"bad time range: {m.group(0)}")
        found.append((start, end))
    return merge_ranges(found)


def parse_gpv(post_id: int, posted_at: datetime, text: str, tz: ZoneInfo) -> GpvPost:
    head, _, body = text.partition(MARKER)
    day = parse_caption_date(head, posted_at, tz)
    if day is None:
        raise OfficialParseError("no date in the post header")
    labels = list(_LABEL_RE.finditer(body))
    if not labels:
        raise OfficialParseError("no queues in the post")
    queues: dict[str, list[tuple[int, int]]] = {}
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
        queues[m.group(1)] = _ranges(r.group(1))
    return GpvPost(post_id, posted_at, day.isoformat(), queues)
