"""Write an iCalendar (.ics) feed that phones can subscribe to."""

from __future__ import annotations

from datetime import datetime

TEXTS = {
    "ru": {
        "summary": "💡 Света не будет ({queue})",
        "description": "Плановое отключение света, очередь {queue}. График берётся из Telegram-канала @{channel}.",
        "alarm": "Свет отключат через {minutes} мин ({queue})",
        "calname": "Отключения света {queue} (Черкассы)",
        "caldesc": "Плановые отключения света для очереди {queue}. Источник: https://t.me/{channel}",
    },
    "uk": {
        "summary": "💡 Світла не буде ({queue})",
        "description": "Планове відключення світла, черга {queue}. Графік береться з Telegram-каналу @{channel}.",
        "alarm": "Світло вимкнуть через {minutes} хв ({queue})",
        "calname": "Відключення світла {queue} (Черкаси)",
        "caldesc": "Планові відключення світла для черги {queue}. Джерело: https://t.me/{channel}",
    },
}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> list[str]:
    """Fold a content line to at most 75 octets without splitting a UTF-8 character."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    parts: list[str] = []
    current = b""
    limit = 75
    for ch in line:
        b = ch.encode("utf-8")
        if len(current) + len(b) > limit:
            parts.append(current.decode("utf-8"))
            current = b""
            limit = 74  # continuation lines start with one space
        current += b
    if current:
        parts.append(current.decode("utf-8"))
    return [parts[0]] + [" " + p for p in parts[1:]]


def build_ics(queue: str, channel: str, events: dict[str, dict], language: str, alarm_minutes: list[int]) -> str:
    t = TEXTS.get(language, TEXTS["ru"])
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//cherkasy-power-outages-calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(t['calname'].format(queue=queue))}",
        f"X-WR-CALDESC:{_escape(t['caldesc'].format(queue=queue, channel=channel))}",
        "X-WR-TIMEZONE:Europe/Kyiv",
        "REFRESH-INTERVAL;VALUE=DURATION:PT15M",
        "X-PUBLISHED-TTL:PT15M",
    ]
    for key in sorted(events):
        ev = events[key]
        start = datetime.strptime(key, "%Y%m%dT%H%M").strftime("%Y%m%dT%H%M00Z")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{queue}-{key}@cherkasy-power-outages-calendar",
            f"DTSTAMP:{ev['modified']}",
            f"LAST-MODIFIED:{ev['modified']}",
            f"SEQUENCE:{ev['seq']}",
            f"DTSTART:{start}",
            f"DTEND:{ev['end']}",
            f"SUMMARY:{_escape(t['summary'].format(queue=queue))}",
            f"DESCRIPTION:{_escape(t['description'].format(queue=queue, channel=channel))}",
            "TRANSP:TRANSPARENT",
            "STATUS:CONFIRMED",
        ]
        for minutes in alarm_minutes:
            lines += [
                "BEGIN:VALARM",
                f"TRIGGER:-PT{minutes}M",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_escape(t['alarm'].format(queue=queue, minutes=minutes))}",
                "END:VALARM",
            ]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(_fold(line))
    return "\r\n".join(folded) + "\r\n"
