"""The page with subscription links (docs/index.html, served by GitHub Pages)."""

from __future__ import annotations

from html import escape
from urllib.parse import quote


def _rows(site_url: str, queues: list[str]) -> str:
    host = site_url.split("://", 1)[1].rstrip("/")
    rows = []
    for q in queues:
        webcal = f"webcal://{host}/{q}.ics"
        google = "https://calendar.google.com/calendar/r?cid=" + quote(webcal, safe="")
        rows.append(
            f'<tr id="q{escape(q)}"><th scope="row">{escape(q)}</th>'
            f'<td><a class="btn" href="{escape(webcal)}">Apple</a></td>'
            f'<td><a class="btn" href="{escape(google)}">Google</a></td>'
            f'<td><a href="{escape(site_url.rstrip("/"))}/{escape(q)}.ics">.ics</a></td></tr>'
        )
    return "\n".join(rows)


def build_index(site_url: str, queues: list[str], channel: str) -> str:
    return f"""<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Відключення світла в Черкасах — календарі</title>
<style>
:root {{ --bg: #ffffff; --fg: #1d2a2e; --muted: #5d6b70; --line: #dde3e5; --accent: #1f7a4d; --accent-fg: #ffffff; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ --bg: #14191b; --fg: #e6eced; --muted: #9aa8ad; --line: #2a3437; --accent: #3fae78; --accent-fg: #0d1210; }}
}}
body {{ margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 36rem; margin: 0 auto; padding: 24px 16px 48px; }}
h1 {{ font-size: 1.4rem; line-height: 1.25; margin: 0 0 8px; }}
p {{ margin: 0 0 12px; color: var(--muted); }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ padding: 10px 6px; border-bottom: 1px solid var(--line); text-align: left; }}
th {{ font-size: 1.1rem; width: 3.5rem; }}
td:last-child {{ text-align: right; font-size: .9rem; }}
a {{ color: var(--accent); }}
.btn {{ display: inline-block; padding: 6px 14px; border-radius: 8px; background: var(--accent); color: var(--accent-fg); text-decoration: none; font-weight: 600; }}
small {{ color: var(--muted); }}
tr:target th, tr:target td {{ background: var(--line); }}
</style>
</head>
<body>
<main>
<h1>Відключення світла в Черкасах: календарі за чергами</h1>
<p>Оберіть свою підчергу і додайте її у календар. Події з'являються і змінюються самі, коли обленерго публікує новий графік. Перед відключенням приходить нагадування за 15 хвилин.</p>
<p>Не знаєте свою чергу? Її можна перевірити за адресою на <a href="https://www.cherkasyoblenergo.com/off">сайті Черкасиобленерго</a>.</p>
<table>
<thead><tr><th scope="col">Черга</th><th scope="col">iPhone, Mac</th><th scope="col">Google Календар</th><th scope="col">Файл</th></tr></thead>
<tbody>
{_rows(site_url, queues)}
</tbody>
</table>
<p><small>Дані беруться з офіційного Telegram-каналу <a href="https://t.me/{escape(channel)}">@{escape(channel)}</a> приблизно раз на 15 хвилин. Телефон оновлює підписку сам, тому зміни можуть з'являтися із запізненням до кількох годин. Календар лише для читання.</small></p>
</main>
</body>
</html>
"""
