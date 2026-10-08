"""Read posts from a public Telegram channel through its web preview (t.me/s/...)."""

from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; cherkasy-power-outages-calendar/1.0)"

MONTHS = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4, "травня": 5, "червня": 6,
    "липня": 7, "серпня": 8, "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}
_DATE_RE = re.compile(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")", re.IGNORECASE)
_PHOTO_RE = re.compile(r"url\(['\"]?([^'\")]+)['\"]?\)")


@dataclass
class Post:
    channel: str
    id: int
    posted_at: datetime  # timezone-aware (UTC)
    text: str
    photo_url: str | None


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_posts(html: str, channel: str) -> list[Post]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[Post] = []
    for node in soup.select(".tgme_widget_message"):
        data_post = node.get("data-post") or ""
        m = re.fullmatch(r"([^/]+)/(\d+)", data_post)
        if not m or m.group(1).lower() != channel.lower():
            continue
        time_tag = node.select_one("time")
        if time_tag is None or not time_tag.get("datetime"):
            continue
        posted_at = datetime.fromisoformat(time_tag["datetime"])
        text_node = node.select_one(".tgme_widget_message_text")
        text = text_node.get_text(" ", strip=True) if text_node else ""
        photo_url = None
        photo = node.select_one(".tgme_widget_message_photo_wrap")
        if photo is not None:
            pm = _PHOTO_RE.search(photo.get("style") or "")
            if pm:
                photo_url = pm.group(1)
        posts.append(Post(channel, int(m.group(2)), posted_at, text, photo_url))
    return posts


def fetch_posts(channel: str, pages: int = 2, fetch=http_get) -> list[Post]:
    """Newest posts of the channel, oldest first. `pages` counts preview pages."""
    collected: dict[int, Post] = {}
    url = f"https://t.me/s/{channel}"
    for _ in range(max(1, pages)):
        html = fetch(url).decode("utf-8", errors="replace")
        page = parse_posts(html, channel)
        if not page:
            break
        for p in page:
            collected[p.id] = p
        url = f"https://t.me/s/{channel}?before={min(p.id for p in page)}"
    return [collected[i] for i in sorted(collected)]


def parse_caption_date(text: str, posted_at: datetime, tz: ZoneInfo) -> date | None:
    """The day a schedule post is about, e.g. '... на 8 жовтня' -> 8 October."""
    m = _DATE_RE.search(text)
    if not m:
        return None
    day, month = int(m.group(1)), MONTHS[m.group(2).lower()]
    local = posted_at.astimezone(tz).date()
    best: date | None = None
    for year in (local.year - 1, local.year, local.year + 1):
        try:
            cand = date(year, month, day)
        except ValueError:
            continue
        if best is None or abs((cand - local).days) < abs((best - local).days):
            best = cand
    if best is None or abs((best - local).days) > 90:
        return None
    return best


_ON_RE = re.compile(r"увімкнуть\s+в\s+(\d{1,2}):(\d{2})", re.IGNORECASE)
_NEXT_RE = re.compile(r"Наступне\s+відключення\s+енергоживлення\s+в\s+(\d{1,2}):(\d{2})", re.IGNORECASE)


def parse_notice(text: str, posted_at: datetime, tz: ZoneInfo) -> tuple[str, datetime] | None:
    """Bot notices like 'Енергоживлення увімкнуть в 09:00' -> ('on', local datetime)."""
    for kind, rx in (("on", _ON_RE), ("off", _NEXT_RE)):
        m = rx.search(text)
        if not m:
            continue
        hh, mm = int(m.group(1)), int(m.group(2))
        local = posted_at.astimezone(tz)
        target = datetime(local.year, local.month, local.day, tzinfo=tz) + timedelta(hours=hh, minutes=mm)
        if target < local - timedelta(minutes=30):
            target += timedelta(days=1)
        return kind, target.replace(tzinfo=None)
    return None
