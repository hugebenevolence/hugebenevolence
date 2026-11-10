"""Contribution skyline for the profile README: the last year of GitHub contributions drawn as a pixel-art night city in the
palette of assets/room.gif.

Each building is one week. Its height grows with that week's contributions, and its seven lowest windows are the seven days,
lit when there was a contribution that day (brighter on busier days). Stars twinkle and a plane crosses the sky.

The data comes from the public contribution calendar (github.com/users/<user>/contributions), so no token is needed. Only
the standard library is used, so the workflow needs no installs. Run:

    python3 assets/build_skyline.py [user] [output.svg]
"""
import math
import re
import sys
import urllib.request
from collections import defaultdict
from html import unescape

U = 2                               # px per pixel-art unit
GW, GH = 288, 72                    # canvas in units (576 x 144 px)
GROUND = 56                         # first ground row
BW, GAP = 4, 1                      # building width and gap, in units
C = {
    "edge": "#181a2c", "sky1": "#161c3e", "sky2": "#202854", "sky3": "#363a6c", "star": "#dce0ff", "glint": "#4c5488",
    "moon": "#f4ecc8", "moon_dk": "#d8ceac", "bld": "#1d2040", "bld2": "#242850", "roof": "#323770", "far": "#2b305f", "win": "#2a2e58", "lit": "#face78",
    "lit_dim": "#ba8c5c", "ground": "#202238", "road": "#2a2c48", "text": "#9aa3d4", "text_dim": "#6a72a8", "plane": "#e05a5a",
}


def fetch(user: str) -> str:
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "profile-skyline"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse(html: str) -> tuple[list[dict], int]:
    """Weeks in calendar order, each {"days": {dow: level}, "count": n}, and the total count."""
    counts = {}
    for target, text in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*([\d,]+) contributions?", unescape(text))
        counts[target] = int(m.group(1).replace(",", "")) if m else 0
    weeks = defaultdict(lambda: {"days": {}, "count": 0})
    for td in re.findall(r"<td[^>]*data-date[^>]*>", html):
        ident = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
        level = re.search(r'data-level="(\d)"', td)
        if not ident or not level:
            continue
        dow, week = int(ident.group(1)), int(ident.group(2))
        weeks[week]["days"][dow] = int(level.group(1))
        weeks[week]["count"] += counts.get(f"contribution-day-component-{dow}-{week}", 0)
    ordered = [weeks[k] for k in sorted(weeks)]
    return ordered, sum(w["count"] for w in ordered)


def rect(x: float, y: float, w: float, h: float, colour: str, child: str = "") -> str:
    attrs = f'x="{x * U:g}" y="{y * U:g}" width="{w * U:g}" height="{h * U:g}" fill="{colour}"'
    return f"<rect {attrs}>{child}</rect>" if child else f"<rect {attrs}/>"


def render(weeks: list[dict], total: int) -> str:
    out = []
    # sky in three bands with dithered seams, then the ground and the road
    out += [rect(0, 0, GW, 18, C["sky1"]), rect(0, 18, GW, 18, C["sky2"]), rect(0, 36, GW, GROUND - 36, C["sky3"])]
    for seam, colour in ((18, "sky1"), (36, "sky2")):
        out += [rect(x, seam, 1, 1, C[colour]) for x in range(seam % 2, GW, 2)]
    out += [rect(0, GROUND, GW, GH - GROUND, C["ground"]), rect(0, GROUND, GW, 1, C["edge"])]
    out += [rect(x, GROUND + 4, 5, 1, C["road"]) for x in range(3, GW, 10)]

    # stars at fixed pseudo-random places; every fifth one twinkles
    for i in range(34):
        x, y = (i * 97 + 13) % (GW - 30) + 4, (i * 53 + 7) % 34 + 2
        anim = ""
        if i % 5 == 0:
            anim = (f'<animate attributeName="opacity" values="1;0.15;1" dur="{2.4 + (i % 3) * 0.7:.1f}s" '
                    f'begin="{(i % 7) * 0.4:.1f}s" repeatCount="indefinite"/>')
        out.append(rect(x, y, 1, 1, C["star" if i % 3 else "glint"], anim))
    # moon
    mx, my = GW - 22, 6
    out += [rect(mx + 1, my, 3, 1, C["moon"]), rect(mx, my + 1, 5, 3, C["moon"]), rect(mx + 1, my + 4, 3, 1, C["moon"]),
            rect(mx + 1, my + 2, 1, 1, C["moon_dk"]), rect(mx + 3, my + 3, 1, 1, C["moon_dk"])]
    # a plane with a blinking light crossing the sky
    blink = '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
    out.append(f'<g><animateTransform attributeName="transform" type="translate" from="{(GW + 10) * U} 0" to="-{20 * U} 0" '
               f'dur="26s" repeatCount="indefinite"/>{rect(0, 10, 4, 1, C["glint"])}{rect(0, 10, 1, 1, C["plane"], blink)}</g>')

    # a faint far skyline for depth (decoration, not data)
    x = 0
    while x < GW:
        w = 5 + (x * 7) % 4
        h = 6 + (x * 13) % 15
        out.append(rect(x, GROUND - h, w, h, C["far"]))
        x += w

    # buildings, one per week
    n = len(weeks)
    peak = max((w["count"] for w in weeks), default=0) or 1
    x0 = (GW - (n * (BW + GAP) - GAP)) // 2
    for i, week in enumerate(weeks):
        x = x0 + i * (BW + GAP)
        h = 3 + round(38 * math.sqrt(week["count"] / peak)) if week["count"] else 2
        top = GROUND - h
        out += [rect(x, top, BW, h, C["bld" if i % 2 else "bld2"]), rect(x, top, BW, 1, C["roof"])]
        rows = list(range(GROUND - 2, top + 1, -2))          # window rows from the bottom up
        for k, y in enumerate(rows):
            if k < 7:
                level = week["days"].get(6 - k, 0)            # bottom window is Saturday, the seventh is Sunday
                colour = C["lit"] if level >= 3 else C["lit_dim"] if level else C["win"]
            else:
                colour = C["win"]
            out.append(rect(x + 1, y, 2, 1, colour))

    caption = f"{total:,} contributions in the last year"
    text = (f'<text x="{6 * U}" y="{(GH - 4) * U}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'font-size="11" fill="{C["text"]}">{caption}</text>'
            f'<text x="{(GW - 6) * U}" y="{(GH - 4) * U}" text-anchor="end" font-family="ui-monospace, SFMono-Regular, '
            f'Menlo, Consolas, monospace" font-size="11" fill="{C["text_dim"]}">each building is a week</text>')
    w, h = GW * U, GH * U
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{caption}, drawn as a night city with one building per week">\n'
            f'<defs><clipPath id="r"><rect width="{w}" height="{h}" rx="10"/></clipPath></defs>\n'
            f'<g clip-path="url(#r)" shape-rendering="crispEdges">\n' + "\n".join(out) + "\n</g>\n" + text + "\n"
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="none" stroke="{C["edge"]}"/>\n</svg>\n')


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else "hugebenevolence"
    path = sys.argv[2] if len(sys.argv) > 2 else "dist/skyline.svg"
    source = sys.argv[3] if len(sys.argv) > 3 else None       # a saved contributions page, for working offline
    html = open(source, encoding="utf-8").read() if source else fetch(user)
    weeks, total = parse(html)
    if not weeks:
        sys.exit("no contribution data found")
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(weeks, total))
    print(f"wrote {path}: {len(weeks)} weeks, {total} contributions")


if __name__ == "__main__":
    main()
