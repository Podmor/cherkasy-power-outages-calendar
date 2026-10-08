from pathlib import Path

import pytest
from PIL import Image

from outage_calendar.wheel import WheelError, parse_wheel

from .render import render_wheel

FIXTURES = Path(__file__).parent / "fixtures"


def test_real_screenshot_9_october():
    # Screenshot of the real channel post: outages 03-05, 13-15, 19-21.
    img = Image.open(FIXTURES / "phone_screenshot_9_oct.png")
    assert parse_wheel(img) == [3, 4, 13, 14, 19, 20]


def test_full_schedule():
    hours = [0, 9, 10, 15, 16, 19, 20]
    assert parse_wheel(render_wheel(hours)) == hours


def test_no_outages_and_all_day_outage():
    assert parse_wheel(render_wheel([])) == []
    assert parse_wheel(render_wheel(list(range(24)))) == list(range(24))


def test_changes_image_pale_and_bright():
    # Final outages: 7-9, 17-19 (pale, unchanged) and 23 (bright, new);
    # 21-23 was an outage that got cancelled (bright green -> power).
    final = [7, 8, 17, 18, 23]
    img = render_wheel(final, kind="changes", added=[23], cancelled=[21, 22])
    assert parse_wheel(img) == final


def test_other_sizes():
    hours = [3, 4, 13, 14]
    assert parse_wheel(render_wheel(hours, size=400)) == hours
    assert parse_wheel(render_wheel(hours, size=1280)) == hours


def test_not_a_wheel_is_rejected():
    with pytest.raises(WheelError):
        parse_wheel(Image.new("RGB", (800, 800), "white"))
    img = Image.new("RGB", (800, 800), "white")
    for x in range(0, 700):
        for y in range(0, 60):
            img.putpixel((x, y), (224, 104, 95))
    with pytest.raises(WheelError):
        parse_wheel(img)
