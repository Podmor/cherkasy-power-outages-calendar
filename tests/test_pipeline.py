"""End-to-end run against a fake channel built from real posts of @cherkasy_blackout_3."""

import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from outage_calendar.main import run

from .render import render_wheel

CAPTION_DAILY_8 = "За розпорядженням НЕК «Укренерго» 8 жовтня з 00:00 до 24:00 у Черкаській області будуть застосовані графіки погодинних відключень (ГПВ)."
CAPTION_DAILY_9 = "Через постійні ворожі обстріли та наслідки попередніх ракетно-дронових атак за розпорядженням НЕК «Укренерго» 9 жовтня з 00:00 до 24:00 у Черкаській області будуть застосовані графіки погодинних відключень (ГПВ)."


def _full(hours):
    return {"hours": hours}


def _changes(final, added=(), cancelled=()):
    return {"hours": final, "kind": "changes", "added": added, "cancelled": cancelled}


# (id, UTC time, text, image spec or None) - ids, times and texts are the real ones.
POSTS = [
    (2408, "2026-10-07T04:05:00", "Енергоживлення увімкнуть в 09:00", None),
    (2409, "2026-10-07T06:05:00", "Наступне відключення енергоживлення в 17:00", None),
    (2411, "2026-10-07T14:05:00", "Енергоживлення увімкнуть в 19:00", None),
    (2412, "2026-10-07T16:16:11", CAPTION_DAILY_8, _full([9, 10, 15, 16])),
    (2413, "2026-10-07T17:57:03", "Оновлений графік погодинних відключень (ГПВ) на 7 жовтня.", _changes([7, 8, 17, 18, 23], [23], [21, 22])),
    (2414, "2026-10-07T19:50:00", "До відключення енергоживлення залишилось 10 хвилин!", None),
    (2415, "2026-10-07T20:05:00", "Енергоживлення увімкнуть в 24:00", None),
    (2416, "2026-10-07T20:53:05", "Оновлений графік погодинних відключень (ГПВ) на 8 жовтня.", _full([0, 9, 10, 15, 16, 19, 20])),
    (2417, "2026-10-07T22:05:00", "Наступне відключення енергоживлення в 09:00", None),
    (2418, "2026-10-08T04:57:03", "Оновлений графік погодинних відключень (ГПВ) на 8 жовтня.", _full([0, 8, 9, 10, 14, 15, 16, 19, 20])),
    (2419, "2026-10-08T05:05:00", "Енергоживлення увімкнуть в 11:00", None),
    (2420, "2026-10-08T08:05:02", "Наступне відключення енергоживлення в 14:00", None),
    (2421, "2026-10-08T10:50:01", "До відключення енергоживлення залишилось 10 хвилин!", None),
    (2422, "2026-10-08T11:05:01", "Енергоживлення увімкнуть в 17:00", None),
    (2423, "2026-10-08T14:05:01", "Наступне відключення енергоживлення в 19:00", None),
    (2424, "2026-10-08T15:50:01", "До відключення енергоживлення залишилось 10 хвилин!", None),
    (2425, "2026-10-08T16:05:02", "Енергоживлення увімкнуть в 21:00", None),
    (2426, "2026-10-08T18:25:06", CAPTION_DAILY_9, _full([3, 4, 13, 14, 19, 20])),
]


class FakeChannel:
    def __init__(self, posts):
        self.posts = list(posts)
        self.image_downloads = 0

    def photo_url(self, post_id):
        return f"https://cdn4.telesco.pe/file/photo-{post_id}.jpg"

    def html(self, url):
        if "before=" in url:
            return b"<html></html>"
        parts = []
        for pid, when, text, spec in self.posts:
            photo = ""
            if spec:
                photo = f'<a class="tgme_widget_message_photo_wrap" style="width:800px;background-image:url(\'{self.photo_url(pid)}\')"></a>'
            parts.append(
                f'<div class="tgme_widget_message_wrap"><div class="tgme_widget_message js-widget_message" data-post="cherkasy_blackout_3/{pid}">'
                f'{photo}<div class="tgme_widget_message_text js-message_text">{text}</div>'
                f'<a class="tgme_widget_message_date"><time datetime="{when}+00:00" class="time">x</time></a></div></div>'
            )
        return ("<html><body>" + "".join(parts) + "</body></html>").encode()

    def bytes(self, url):
        self.image_downloads += 1
        pid = int(url.rsplit("photo-", 1)[1].split(".")[0])
        spec = next(s for p, _, _, s in self.posts if p == pid)
        img = render_wheel(spec["hours"], kind=spec.get("kind", "full"), added=spec.get("added", ()), cancelled=spec.get("cancelled", ()))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    shutil.copy(Path(__file__).parent.parent / "config.json", root / "config.json")
    return root


def _events(root):
    text = (root / "docs" / "3.1.ics").read_bytes().decode("utf-8")
    events, cur = [], None
    for line in text.replace("\r\n ", "").split("\r\n"):
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            events.append(cur)
            cur = None
        elif cur is not None and ":" in line and not line.startswith(("BEGIN", "END", "TRIGGER", "ACTION")):
            k, v = line.split(":", 1)
            cur[k] = v
    return text, events


NOW = datetime(2026, 10, 8, 18, 30, tzinfo=timezone.utc)


def test_full_run_on_real_posts(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel(POSTS)
    logs = []
    assert run(root, ch.html, ch.bytes, NOW, logs.append) == 0
    assert not [m for m in logs if m.startswith("warning")], logs

    state = json.loads((root / "state" / "3.1.json").read_text(encoding="utf-8"))
    assert state["days"]["2026-10-07"]["hours"] == [7, 8, 17, 18, 23]
    assert state["days"]["2026-10-08"]["hours"] == [0, 8, 9, 10, 14, 15, 16, 19, 20]  # latest update wins
    assert state["days"]["2026-10-08"]["post"] == 2418
    assert state["days"]["2026-10-09"]["hours"] == [3, 4, 13, 14, 19, 20]

    text, events = _events(root)
    # Kyiv is UTC+3 in October (summer time until 25 Oct), so 07:00 Kyiv = 04:00 UTC.
    spans = [(e["DTSTART"], e["DTEND"]) for e in events]
    assert spans == [
        ("20261007T040000Z", "20261007T060000Z"),  # 07-09
        ("20261007T140000Z", "20261007T160000Z"),  # 17-19
        ("20261007T200000Z", "20261007T220000Z"),  # 23:00 on 7th - 01:00 on 8th, merged across midnight
        ("20261008T050000Z", "20261008T080000Z"),  # 08-11
        ("20261008T110000Z", "20261008T140000Z"),  # 14-17
        ("20261008T160000Z", "20261008T180000Z"),  # 19-21
        ("20261009T000000Z", "20261009T020000Z"),  # 03-05
        ("20261009T100000Z", "20261009T120000Z"),  # 13-15
        ("20261009T160000Z", "20261009T180000Z"),  # 19-21
    ]
    assert "TRIGGER:-PT15M" in text
    assert all(len(line.encode("utf-8")) <= 75 for line in text.replace("\r\n", "\n").split("\n"))
    assert text.endswith("\r\n")


def test_second_run_changes_nothing_and_downloads_nothing(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel(POSTS)
    run(root, ch.html, ch.bytes, NOW, lambda m: None)
    first = ((root / "docs" / "3.1.ics").read_bytes(), (root / "state" / "3.1.json").read_bytes())
    downloads = ch.image_downloads

    later = datetime(2026, 10, 8, 19, 0, tzinfo=timezone.utc)
    run(root, ch.html, ch.bytes, later, lambda m: None)
    assert ch.image_downloads == downloads
    assert ((root / "docs" / "3.1.ics").read_bytes(), (root / "state" / "3.1.json").read_bytes()) == first


def test_schedule_update_edits_and_removes_events(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel(POSTS)
    run(root, ch.html, ch.bytes, NOW, lambda m: None)

    # A new image for 9 Oct: 03-05 is cancelled, 13-15 is extended to 13-16, 19-21 stays, 22-23 is added.
    update = (2427, "2026-10-09T05:00:00", "Оновлений графік погодинних відключень (ГПВ) на 9 жовтня.",
              _changes([13, 14, 15, 19, 20, 22], added=[15, 22], cancelled=[3, 4]))
    ch.posts.append(update)
    later = datetime(2026, 10, 9, 5, 5, tzinfo=timezone.utc)
    assert run(root, ch.html, ch.bytes, later, lambda m: None) == 0

    _, events = _events(root)
    spans = {e["DTSTART"]: e for e in events}
    assert "20261009T000000Z" not in spans  # cancelled outage disappeared
    assert spans["20261009T100000Z"]["DTEND"] == "20261009T130000Z"  # extended to 16:00 Kyiv
    assert spans["20261009T100000Z"]["SEQUENCE"] == "1"
    assert spans["20261009T160000Z"]["SEQUENCE"] == "0"  # untouched
    assert spans["20261009T190000Z"]["DTEND"] == "20261009T200000Z"  # new outage 22:00-23:00 Kyiv
    assert spans["20261009T190000Z"]["SEQUENCE"] == "0"


def test_unreadable_newest_image_fails_the_run(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel(POSTS)

    class Broken(FakeChannel):
        def bytes(self, url):
            from PIL import Image
            buf = io.BytesIO()
            Image.new("RGB", (800, 800), "white").save(buf, "PNG")
            return buf.getvalue()

    broken = Broken(POSTS)
    logs = []
    assert run(root, broken.html, broken.bytes, NOW, logs.append) == 1
    assert any("cannot read the image" in m for m in logs)
