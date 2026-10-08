"""Read an outage-schedule "wheel" image into a list of outage hours.

The channels publish a round 24-hour clock: hour 0 at the top, going clockwise,
one 15-degree sector per hour. Hour N occupies the sector that starts at the
label N. Sectors are red (no power) or green (power). In "changes" images the
unchanged sectors are pale and the changed ones are bright:

* bright red   - a new outage            -> outage
* pale red     - an unchanged outage     -> outage
* pale green   - unchanged, power is on  -> power
* bright green - an outage was cancelled -> power

So in every format "reddish" means no power and "greenish" means power.
"""

from __future__ import annotations

import math

from PIL import Image


class WheelError(Exception):
    """The image does not look like a readable schedule wheel."""


def classify(r: int, g: int, b: int) -> str | None:
    """Return 'red', 'green' or None (white, grey, text, anything else)."""
    mx, mn = max(r, g, b), min(r, g, b)
    c = mx - mn
    if c < 14 or mx < 120:
        return None
    if mx == r:
        h = 60 * (((g - b) / c) % 6)
    elif mx == g:
        h = 60 * ((b - r) / c + 2)
    else:
        h = 60 * ((r - g) / c + 4)
    if h < 0:
        h += 360
    if h <= 22 or h >= 340:
        return "red"
    if 80 <= h <= 165:
        return "green"
    return None


# Where inside a sector we sample: several angles (avoiding the divider lines at
# +-7.5 degrees) and several radii (the ring spans roughly 0.5R..1.0R; the hour
# labels sit on the dividers and the bulb icons are light, so a vote ignores them).
_ANGLE_OFFSETS = (-4, -2, 0, 2, 4)
_RADIUS_FRACTIONS = (0.58, 0.66, 0.74, 0.82, 0.90)


def parse_wheel(image: Image.Image) -> list[int]:
    """Return the sorted list of hours (0-23) with no power."""
    img = image.convert("RGB")
    w, h = img.size
    px = img.load()

    def cls(x: int, y: int) -> str | None:
        if x < 0 or y < 0 or x >= w or y >= h:
            return None
        r, g, b = px[x, y]
        return classify(r, g, b)

    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if cls(x, y) is not None:
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    if maxx < 0:
        raise WheelError("no red/green pixels found")

    bw, bh = maxx - minx, maxy - miny
    if min(bw, bh) < 100 or abs(bw - bh) > 0.12 * max(bw, bh):
        raise WheelError(f"colored area is not a circle ({bw}x{bh})")

    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    radius = max(bw, bh) / 2

    outage: list[int] = []
    total_samples = len(_ANGLE_OFFSETS) * len(_RADIUS_FRACTIONS)
    for n in range(24):
        red = green = 0
        for da in _ANGLE_OFFSETS:
            a = math.radians(15 * n + 7.5 + da)
            for rf in _RADIUS_FRACTIONS:
                x = round(cx + math.sin(a) * rf * radius)
                y = round(cy - math.cos(a) * rf * radius)
                k = cls(x, y)
                if k == "red":
                    red += 1
                elif k == "green":
                    green += 1
        if red + green < total_samples * 0.55:
            raise WheelError(f"hour {n}: sector is unreadable ({red} red, {green} green)")
        if min(red, green) > total_samples * 0.2:
            raise WheelError(f"hour {n}: sector is ambiguous ({red} red, {green} green)")
        if red > green:
            outage.append(n)
    return outage
