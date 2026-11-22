import base64
import json
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
USER = "ASHxOnAIR-MEH"
DATA = ROOT / "data/contributions.json"
CARDS = ROOT / "cards"
BLUE = "#e6b450"
PROJECTS = [
    ("BIO-AI", "BIO-AI", "Explore the BIO-AI project"),
    ("RINK-KSUM-", "RINK", "Discover research technology in Kerala"),
    ("GSMS-G-Gaiter-Service-Management-System-", "G-Gaiter", "Service management system"),
    ("RINK-TECHNOLOGY-EXPLORER-", "RINK Technology", "Explore research technology"),
]


def refresh():
    if "--import" in sys.argv:
        html = Path(sys.argv[sys.argv.index("--import") + 1]).read_text(encoding="utf-8")
    else:
        request = Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-calendar"})
        with urlopen(request, timeout=30) as response:
            html = response.read().decode()
    cells = dict((key, day) for day, key in re.findall(r'data-date="([\d-]+)"[^>]* id="([^"]+)"', html))
    counts = {cells[key]: int(n.replace(",", "")) if n != "No" else 0
              for key, n in re.findall(r'<tool-tip[^>]* for="([^"]+)"[^>]*>\s*(No|[\d,]+) contributions? on', html) if key in cells}
    dates = sorted(map(date.fromisoformat, counts))
    if len(dates) < 350 or len(counts) != len(cells) or (dates[-1] - dates[0]).days + 1 != len(dates):
        raise ValueError("Incomplete contribution calendar")
    DATA.write_text(json.dumps(counts, sort_keys=True, indent=2) + "\n")


def label(x, y, value, size=20, family="Arial", color="#e8edf2"):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}">{escape(str(value))}</text>'


def card(name, width, height, body, delay=0, background="#111820"):
    font = base64.b64encode((ROOT / "fonts/instrument.woff").read_bytes()).decode()
    motion = "" if os.getenv("STATIC") == "1" else f"""@media(prefers-reduced-motion:no-preference){{
    .entry{{animation:arrive .6s {delay}s backwards}} .mark{{animation:arrive .4s var(--delay) backwards}}
    @keyframes arrive{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}}}"""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><style>@font-face{{font-family:Instrument;src:url(data:font/woff;base64,{font}) format("woff")}}{motion}</style><rect width="100%" height="100%" fill="{background}"/><g class="entry">{body}</g></svg>'
    (CARDS / f"{name}.svg").write_text(svg, encoding="utf-8")


def render():
    CARDS.mkdir(exist_ok=True)
    days = sorted((date.fromisoformat(d), n) for d, n in json.loads(DATA.read_text()).items())
    total = sum(n for _, n in days)
    origin = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    grid = label(30, 43, f"{total:,} contributions", 37, "Instrument")
    palette = ["#cde5d4", "#84df98", "#61d47c", "#41c563", "#23ac4e"]
    peak = max(n for _, n in days)
    for day, n in days:
        week, row = divmod((day - origin).days, 7)
        color = palette[0 if not n else min(4, 1 + (4 * (n - 1) // max(1, peak)))]
        grid += f'<rect class="mark" style="--delay:{.12 + week*.009:.3f}s" x="{30+week*15.5}" y="{62+row*15}" width="12" height="12" rx="2" fill="{color}"><title>{day}: {n}</title></rect>'
    card("calendar", 900, 200, grid + label(30, 185, f"{days[0][0]}  /  {days[-1][0]}", 14), .1)


if __name__ == "__main__":
    if "--refresh" in sys.argv or "--import" in sys.argv:
        refresh()
    render()
