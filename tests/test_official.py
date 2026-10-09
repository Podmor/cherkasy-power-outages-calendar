from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from outage_calendar.official import OfficialParseError, parse_gpv
from outage_calendar.telegram import parse_posts

from .official_fixture import FakeChannel, HEAD_UPD_8, NOISE, POSTS, post_html

TZ = ZoneInfo("Europe/Kyiv")


def _h(*hours):
    """Whole hours as (start, end) minute ranges, touching ones joined."""
    from outage_calendar.official import merge_ranges
    return merge_ranges((h * 60, h * 60 + 60) for h in hours)


def _parse(text, when="2026-10-08T04:54:33", pid=1):
    return parse_gpv(pid, datetime.fromisoformat(when + "+00:00"), text, TZ)


def test_real_posts_are_parsed_from_the_page_html():
    posts = parse_posts(FakeChannel().html("https://t.me/s/pat_cherkasyoblenergo").decode(), "pat_cherkasyoblenergo")
    by_id = {p.id: p for p in posts}
    p = parse_gpv(1794, by_id[1794].posted_at, by_id[1794].text, TZ)
    assert p.day == "2026-10-07"
    assert len(p.queues) == 12
    assert p.queues["3.1"] == _h(7, 8, 17, 18)
    assert p.queues["5.1"] == _h(0, 11, 12, 19, 20)
    assert p.queues["6.2"] == _h(13, 14, 21)


def test_times_not_on_a_whole_hour_are_read():
    # Real post of 9 Oct 16:57 Kyiv: outages start and end on the half hour.
    p = _parse(post_html(HEAD_UPD_8, ["1.1 15:00 - 17:00, 20:00 - 22:30", "2.1 16:30 - 19:00", "4.2 15:00 - 17:30, 21:30 - 24:00"]))
    assert p.queues["1.1"] == [(900, 1020), (1200, 1350)]
    assert p.queues["2.1"] == [(990, 1140)]
    assert p.queues["4.2"] == [(900, 1050), (1290, 1440)]


def test_range_ending_at_midnight_is_written_both_ways():
    a = _parse(post_html(HEAD_UPD_8, ["1.1 23:00 - 24:00", "1.2 23:00 - 00:00"]))
    assert a.queues["1.1"] == _h(23) and a.queues["1.2"] == _h(23)


def test_queue_missing_from_a_post_is_not_in_the_result():
    p = _parse(post_html(HEAD_UPD_8, ["1.1 10:00 - 11:00", "2.1 12:00 - 14:00"]))
    assert set(p.queues) == {"1.1", "2.1"}


def test_text_with_the_lines_run_together_is_read_too():
    # textContent of the page without separators: "...- 24:001.2 01:00..."
    text = "Оновлений графік (ГПВ) на 8 жовтня. Години відсутності електропостачання: 1.1 22:00 - 24:00 1.2 01:00 - 03:00, 05:00 - 06:00 Перелік адрес"
    p = _parse(text)
    assert p.queues == {"1.1": _h(22, 23), "1.2": _h(1, 2, 5)}


@pytest.mark.parametrize("lines", [
    ["1.1 14:07 - 16:00"],  # not on a 5-minute mark
    ["1.1 14:70 - 16:00"],  # minutes out of range
    ["1.1 17:00 - 15:00"],  # backwards
    ["1.1 abc"],
])
def test_unreadable_posts_raise(lines):
    with pytest.raises(OfficialParseError):
        _parse(post_html(HEAD_UPD_8, lines))


def test_post_without_a_date_or_queues_raises():
    with pytest.raises(OfficialParseError):
        _parse("Графік (ГПВ). Години відсутності електропостачання: 1.1 10:00 - 11:00")
    with pytest.raises(OfficialParseError):
        _parse("Оновлений графік на 8 жовтня. Години відсутності електропостачання: тут нічого немає")


def test_noise_posts_are_not_schedules():
    from outage_calendar.official import is_gpv
    assert not any(is_gpv(h) for _, _, h, _ in NOISE)
    assert all(is_gpv(post_html(h, lines)) for _, _, h, lines in POSTS)
