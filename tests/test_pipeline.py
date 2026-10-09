"""End-to-end runs against a fake channel built from real posts of @pat_cherkasyoblenergo."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from outage_calendar import ics
from outage_calendar.main import run

from .official_fixture import FakeChannel, HEAD_UPD_9, POSTS, post_html

NOW = datetime(2026, 10, 8, 22, 30, tzinfo=timezone.utc)
ROOT = Path(__file__).parent.parent
QUEUES = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    shutil.copy(ROOT / "config.json", root / "config.json")
    return root


def _state(root, queue):
    return json.loads((root / "state" / f"{queue}.json").read_text(encoding="utf-8"))


def _days(root, queue):
    return {k: v["hours"] for k, v in _state(root, queue)["days"].items()}


def _events(root, queue="3.1"):
    text = (root / "docs" / f"{queue}.ics").read_bytes().decode("utf-8")
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


def test_config_lists_the_twelve_subqueues():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert cfg["queues"] == QUEUES


def test_full_run_on_real_posts(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel()
    logs = []
    assert run(root, ch.html, NOW, logs.append) == 0
    assert not [m for m in logs if "cannot read" in m], logs

    # 3.1: exactly what was read earlier from the pictures of @cherkasy_blackout_3.
    assert _days(root, "3.1") == {
        "2026-10-06": [19, 20],
        "2026-10-07": [7, 8, 17, 18, 23],  # evening update adds 23, keeps the morning and afternoon outages
        "2026-10-08": [0, 8, 9, 10, 14, 15, 16, 19, 20],  # two partial updates merged into the day
        "2026-10-09": [3, 4, 13, 14, 19, 20],
    }
    # Other subqueues, including ones that have no picture channel.
    assert _days(root, "5.2")["2026-10-08"] == [3, 4, 9, 10, 13, 14, 15, 19, 20, 23]
    assert _days(root, "6.1")["2026-10-09"] == [6, 7, 14, 15, 20, 21]  # update after midnight replaces the day
    assert _days(root, "6.1")["2026-10-06"] == [18, 19]  # appears only in the 14:48 update
    assert _days(root, "1.1")["2026-10-06"] == [15, 16, 22, 23]

    for q in QUEUES:
        assert (root / "docs" / f"{q}.ics").exists()
    page = (root / "docs" / "index.html").read_text(encoding="utf-8")
    for q in QUEUES:
        assert f"webcal://podmor.github.io/cherkasy-power-outages-calendar/{q}.ics" in page
        assert f"calendar.google.com/calendar/r?cid=webcal%3A%2F%2Fpodmor.github.io%2Fcherkasy-power-outages-calendar%2F{q}.ics" in page


def test_ics_of_queue_3_1(tmp_path):
    root = _project(tmp_path)
    run(root, FakeChannel().html, NOW, lambda m: None)
    text, events = _events(root)
    # Kyiv is UTC+3 in October (summer time until 25 Oct), so 07:00 Kyiv = 04:00 UTC.
    spans = [(e["DTSTART"], e["DTEND"]) for e in events]
    assert spans == [
        ("20261006T160000Z", "20261006T180000Z"),  # 19-21 on the 6th
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
    assert "X-WR-CALNAME:Відключення світла 3.1 (Черкаси)" in text
    assert events[0]["SUMMARY"] == "💡 Світла не буде (3.1)"
    assert "TRIGGER:-PT15M" in text
    assert all(len(line.encode("utf-8")) <= 75 for line in text.replace("\r\n", "\n").split("\n"))
    assert text.endswith("\r\n")


def test_output_uses_only_ukrainian_letters(tmp_path):
    root = _project(tmp_path)
    run(root, FakeChannel().html, NOW, lambda m: None)
    for path in list((root / "docs").iterdir()) + list((root / "state").iterdir()):
        text = path.read_bytes().decode("utf-8")
        assert not re.search("[ыэъёЫЭЪЁ]", text), path


def test_second_run_changes_nothing(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel()
    run(root, ch.html, NOW, lambda m: None)
    first = {p.name: p.read_bytes() for d in ("docs", "state") for p in (root / d).iterdir()}
    run(root, ch.html, datetime(2026, 10, 8, 23, 0, tzinfo=timezone.utc), lambda m: None)
    second = {p.name: p.read_bytes() for d in ("docs", "state") for p in (root / d).iterdir()}
    assert first == second


def test_schedule_update_edits_and_removes_events(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel()
    run(root, ch.html, NOW, lambda m: None)

    # 9 Oct, 08:05 Kyiv: 03-05 has passed, 13-15 is extended to 13-16, 19-21 stays, 22-23 is added.
    update = (1808, "2026-10-09T05:05:00", HEAD_UPD_9, [
        "3.1 13:00 - 16:00, 19:00 - 21:00, 22:00 - 23:00",
    ])
    ch.posts.append(update)
    assert run(root, ch.html, datetime(2026, 10, 9, 5, 10, tzinfo=timezone.utc), lambda m: None) == 0

    assert _days(root, "3.1")["2026-10-09"] == [3, 4, 13, 14, 15, 19, 20, 22]  # 03-05 already happened: kept
    _, events = _events(root)
    spans = {e["DTSTART"]: e for e in events}
    assert spans["20261009T100000Z"]["DTEND"] == "20261009T130000Z"  # extended to 16:00 Kyiv
    assert spans["20261009T100000Z"]["SEQUENCE"] == "1"
    assert spans["20261009T160000Z"]["SEQUENCE"] == "0"  # untouched
    assert spans["20261009T190000Z"]["DTEND"] == "20261009T200000Z"  # new outage 22:00-23:00 Kyiv
    assert spans["20261009T190000Z"]["SEQUENCE"] == "0"

    # An update that cancels the rest of the day: nothing is listed for 3.1 any more.
    ch.posts.append((1809, "2026-10-09T10:00:00", HEAD_UPD_9, ["1.1 20:00 - 21:00"]))
    run(root, ch.html, datetime(2026, 10, 9, 10, 5, tzinfo=timezone.utc), lambda m: None)
    assert _days(root, "3.1")["2026-10-09"] == [3, 4]  # at 13:00 Kyiv only the morning outage is left
    _, events = _events(root)
    assert "20261009T100000Z" not in {e["DTSTART"] for e in events}


def test_unreadable_newest_post_fails_the_run(tmp_path):
    root = _project(tmp_path)
    ch = FakeChannel(POSTS + [(1810, "2026-10-09T10:00:00", HEAD_UPD_9, ["3.1 14:30 - 16:00"])])
    logs = []
    assert run(root, ch.html, NOW, logs.append) == 1
    assert any("post 1810" in m for m in logs)
    # The older posts were still applied.
    assert _days(root, "3.1")["2026-10-09"] == [3, 4, 13, 14, 19, 20]


def test_unreadable_old_post_does_not_fail_forever(tmp_path):
    root = _project(tmp_path)
    broken = (1793, "2026-10-06T15:00:00", "Оновлений графік (ГПВ) на 6 жовтня. ", ["1.1 14:30 - 16:00"])
    ch = FakeChannel(POSTS + [broken])
    assert run(root, ch.html, NOW, lambda m: None) == 0


def test_changed_texts_mark_events_as_modified(tmp_path, monkeypatch):
    root = _project(tmp_path)
    ch = FakeChannel()
    run(root, ch.html, NOW, lambda m: None)
    assert {e["SEQUENCE"] for e in _events(root)[1]} == {"0"}

    monkeypatch.setitem(ics.TEXTS, "summary", "💡 Світла не буде! ({queue})")
    later = datetime(2026, 10, 8, 23, 0, tzinfo=timezone.utc)
    run(root, ch.html, later, lambda m: None)
    text, events = _events(root)
    assert "Світла не буде! (3.1)" in text
    assert {e["SEQUENCE"] for e in events} == {"1"}
    assert {e["LAST-MODIFIED"] for e in events} == {"20261008T230000Z"}

    before = (root / "docs" / "3.1.ics").read_bytes()
    run(root, ch.html, datetime(2026, 10, 8, 23, 15, tzinfo=timezone.utc), lambda m: None)
    assert (root / "docs" / "3.1.ics").read_bytes() == before


def test_state_from_the_picture_channel_is_migrated(tmp_path):
    """The live calendar of queue 3.1 was built from pictures: its events keep their numbers."""
    root = _project(tmp_path)
    (root / "state").mkdir()
    old_state = {
        "queue": "3.1",
        "language": "uk",
        "days": {"2026-10-09": {"hours": [1], "post": 99999, "photo": "x", "posted_at": "2026-10-08T18:25:06+00:00"}},
        "events": {
            "20261009T0000": {"end": "20261009T020000Z", "seq": 1, "modified": "20261008T231641Z"},
            "20261009T1000": {"end": "20261009T120000Z", "seq": 1, "modified": "20261008T231641Z"},
            "20261009T1600": {"end": "20261009T180000Z", "seq": 1, "modified": "20261008T231641Z"},
        },
    }
    (root / "state" / "3.1.json").write_text(json.dumps(old_state), encoding="utf-8")
    run(root, FakeChannel().html, NOW, lambda m: None)

    assert _days(root, "3.1")["2026-10-09"] == [3, 4, 13, 14, 19, 20]  # the stale day is replaced by the channel's data
    _, events = _events(root)
    spans = {e["DTSTART"]: e for e in events}
    assert spans["20261009T000000Z"]["SEQUENCE"] == "2"  # same time as before, only the texts changed
    assert spans["20261009T100000Z"]["SEQUENCE"] == "2"
    assert "language" not in _state(root, "3.1")
