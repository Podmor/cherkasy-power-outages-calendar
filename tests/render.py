"""Draw synthetic schedule wheels for tests (same geometry as the channel images)."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

RED = (224, 104, 95)
GREEN = (143, 201, 122)
PALE_RED = (214, 170, 166)
PALE_GREEN = (190, 208, 186)


def render_wheel(outage_hours, kind="full", cancelled=(), added=(), size=800) -> Image.Image:
    """kind='full': plain day schedule. kind='changes': unchanged sectors pale,
    `added` hours bright red (new outage), `cancelled` hours bright green."""
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)
    box = (0, 0, size - 1, size - 1)
    for n in range(24):
        is_out = n in outage_hours
        if kind == "full":
            color = RED if is_out else GREEN
        else:
            if n in added:
                color = RED
            elif n in cancelled:
                color = GREEN
            else:
                color = PALE_RED if is_out else PALE_GREEN
        d.pieslice(box, 15 * n - 90, 15 * n - 75, fill=color)
    c = size / 2
    # divider lines
    for n in range(24):
        a = math.radians(15 * n)
        d.line([(c, c), (c + math.sin(a) * c, c - math.cos(a) * c)], fill="white", width=3)
    # bulb icons (light blobs) on the middle of every sector
    for n in range(24):
        a = math.radians(15 * n + 7.5)
        x, y = c + math.sin(a) * 0.62 * c, c - math.cos(a) * 0.62 * c
        if n not in outage_hours:
            d.ellipse((x - 14, y - 18, x + 14, y + 12), outline=(235, 245, 235), width=3)
    # hour labels: white circles on the dividers
    for n in range(24):
        a = math.radians(15 * n)
        x, y = c + math.sin(a) * 0.87 * c, c - math.cos(a) * 0.87 * c
        d.ellipse((x - 20, y - 20, x + 20, y + 20), fill="white")
        d.text((x - 6, y - 6), str(n), fill=(40, 50, 55))
    # inner white circle with the queue title
    r = 0.5 * c
    d.ellipse((c - r, c - r, c + r, c + r), fill="white")
    d.text((c - 20, c - 10), "3.1", fill=(40, 50, 55))
    return img
