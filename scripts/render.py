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
BLUE = "#244cce"
PROJECTS = [
    ("RINK-KSUM-", "RINK", "Discover research technology in Kerala"),
    ("IMA-Parippally-Webinar-Registration-Website", "IMA Parippally", "Webinar registration website"),
    ("MINNAL-TECHNOLOGY-LAB", "Minnal Technology Lab", "Technology lab website"),
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


def label(x, y, value, size=20, family="Arial", color="#202322"):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}">{escape(str(value))}</text>'


def card(name, width, height, body, delay=0, background="#f8f5ec"):
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
    card("hero", 900, 198, label(36, 42, "@ASHxOnAIR-MEH", 18, color=BLUE) +
         label(33, 121, "Muhammed Ashik S", 81, "Instrument") +
         label(36, 165, "Building websites for research discovery, events and creative portfolios.", 21))
    origin = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    grid = label(30, 43, f"{total:,} contributions", 37, "Instrument")
    palette = ["#e5e7e1", "#bbcafa", "#839ff1", "#496ee0", BLUE]
    peak = max(n for _, n in days)
    for day, n in days:
        week, row = divmod((day - origin).days, 7)
        color = palette[0 if not n else min(4, 1 + (4 * (n - 1) // max(1, peak)))]
        grid += f'<rect class="mark" style="--delay:{.12 + week*.009:.3f}s" x="{30+week*15.5}" y="{62+row*15}" width="12" height="12" rx="2" fill="{color}"><title>{day}: {n}</title></rect>'
    card("calendar", 900, 200, grid + label(30, 185, f"{days[0][0]}  /  {days[-1][0]}", 14), .1)
    months = Counter()
    streak = longest = 0
    for day, n in days:
        months[day.strftime("%Y-%m")] += n
        streak = streak + 1 if n else 0
        longest = max(longest, streak)
    busiest, count = max(days, key=lambda item: item[1])
    body = label(30, 43, "Activity by month", 37, "Instrument")
    for i, (month, n) in enumerate(months.items()):
        x = 32 + i * 835 / len(months)
        h = 78 * n / max(1, max(months.values()))
        fill = BLUE if n and n == max(months.values()) else "#9daabf"
        body += f'<rect class="mark" style="--delay:{.36+i*.025}s" x="{x}" y="{152-h}" width="32" height="{h}" fill="{fill}"/>' + label(x, 146-h, n, 13) + label(x, 174, date.fromisoformat(month+"-01").strftime("%b"), 14)
    stats = f"{sum(n>0 for _, n in days)} active days     /     Longest streak: {longest} days     /     Peak: {count} on {busiest}"
    card("months", 900, 224, body + label(30, 209, stats, 19), .3)
    profile = f"https://github.com/{USER}"
    readme = [f'# Muhammed Ashik S', '', '![Muhammed Ashik S builds websites for research discovery, events and portfolios](cards/hero.svg)', '', f'![{total} GitHub contributions](cards/calendar.svg)', '', f'![Monthly activity. {stats}](cards/months.svg)', '']
    tiles = [("Build", "Research tools", "#cfddff"), ("Connect", "Event websites", "#ffc6aa"), ("Explore", "Creative portfolios", "#f4df86")]
    links = [profile+"/"+PROJECTS[0][0], profile+"/"+PROJECTS[1][0], profile+"/alan-varkala-portfolio"]
    for i, ((title, subtitle, bg), link) in enumerate(zip(tiles, links)):
        card(title.lower(), 290, 140, label(20, 65, title, 54, "Instrument") + label(22, 110, subtitle) + label(248, 38, "↗", 25), .6+i*.1, bg)
        readme.append(f'<a href="{link}"><img src="cards/{title.lower()}.svg" width="32.5%" alt="{title} — {subtitle}"></a>')
    readme += ["", "## Featured repositories", ""]
    for i, (slug, title, desc) in enumerate(PROJECTS):
        card(f"project-{i}", 900, 94, label(30, 57, title, 39, "Instrument") + label(400, 54, desc, 20) + label(844, 54, "↗", 26, color=BLUE), .85+i*.08)
        readme.extend([f'[![{title} — {desc}](cards/project-{i}.svg)]({profile}/{slug})', ''])
    (ROOT / "README.md").write_text("\n".join(readme), encoding="utf-8")


if __name__ == "__main__":
    if "--refresh" in sys.argv or "--import" in sys.argv:
        refresh()
    render()
