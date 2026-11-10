"""Pixel-art hero for the profile README: a room through one day, from morning to night and back.

The sun crosses the window, the sky turns to sunset, the room dims to blue, the desk lamp and the city lights come on, the
moon and the stars come out, then dawn. Meanwhile the developer works through "Attention Is All You Need" (the monitor shows
the paper and its Transformer figure), picks up a printed paper, gets stuck, gets the idea, and a check appears. The cat is
awake by day and asleep at night.

The framed painting on the wall is the owner's last year on GitHub: one column per week, taller for busier weeks, with a lit
window for each active day; a small plaque under it reads MY YEAR ON GITHUB. The data comes from the public contribution calendar, so the GIF is redrawn daily by
.github/workflows/room.yml.

The scene is drawn on a 192 x 64 grid and scaled x5 with nearest-neighbour (960 x 320 px). Every surface has one daytime
colour and is tinted towards indigo by the same rule as night falls, so the palette stays coherent at every hour. Needs
Pillow:

    python3 assets/build_room.py [user] [output.gif] [saved contributions page]
"""
import math
import os
import re
import sys
import urllib.request
from collections import defaultdict
from html import unescape

from PIL import Image, ImageDraw

W, H, SCALE, FRAMES, MS = 192, 64, 5, 80, 100
KEY = (255, 0, 255)                                   # transparent corner colour, palette index 0
EDGE = (36, 34, 52)

DAY = {   # surfaces in daylight; night is derived from these by night()
    "wall": (232, 222, 204), "wainscot": (176, 192, 166), "trim": (150, 166, 140), "base": (120, 96, 82),
    "floor": (192, 148, 110), "floor_ln": (168, 126, 94),
    "frame": (150, 108, 84), "frame_dk": (120, 84, 66), "curtain": (206, 128, 128), "curtain_dk": (176, 104, 108),
    "rod": (92, 70, 62), "pot": (196, 120, 96), "plant": (96, 166, 104), "plant_dk": (70, 128, 82),
    "cork": (196, 150, 104), "board_edge": (120, 90, 66), "note_y": (244, 214, 112), "note_p": (238, 152, 170),
    "note_m": (142, 212, 172), "note_b": (132, 182, 240), "pin": (214, 72, 72), "note_ln": (180, 170, 160),
    "clock": (250, 248, 240), "rim": (64, 60, 76), "hand": (44, 44, 60),
    "gold": (212, 172, 96), "gold_dk": (164, 126, 66),
    "desk": (176, 128, 92), "desk_dk": (146, 104, 74), "bin": (120, 130, 166), "bin_dk": (98, 106, 142),
    "paper": (248, 246, 238), "paper_ln": (176, 178, 192), "fig": (110, 170, 255), "print_ink": (52, 54, 70),
    "book1": (200, 96, 86), "book2": (90, 138, 182), "book3": (226, 186, 100), "book4": (118, 166, 118),
    "book5": (160, 118, 172), "duck": (255, 214, 90), "beak": (232, 130, 80),
    "chair": (84, 96, 128), "chair_dk": (66, 76, 104),
    "hood": (70, 118, 152), "hood_dk": (54, 96, 128), "pants": (60, 64, 92), "shoe": (240, 240, 244),
    "skin": (238, 198, 162), "skin_dk": (210, 164, 132), "hair": (44, 32, 36), "eye": (32, 30, 40),
    "key": (90, 94, 120), "key_hi": (130, 134, 162), "mon": (42, 44, 60), "mug": (244, 244, 248), "steam": (196, 200, 216),
    "lamp": (170, 176, 200), "shade": (220, 120, 90), "shade_dk": (182, 96, 74), "bulb_off": (236, 228, 210),
    "cat": (182, 182, 198), "cat_dk": (132, 132, 152), "cat_bed": (174, 104, 128), "cat_bed_dk": (140, 80, 104),
}
EMIT = {  # light sources and screens, never darkened
    "screen": (18, 22, 38), "axis": (84, 92, 128), "ok": (60, 170, 90), "c_text": (196, 202, 220),
    "page": (246, 246, 240), "ink": (52, 54, 70), "ink_lt": (150, 152, 166), "nx": (190, 192, 200),
    "emb": (232, 150, 150), "attn": (240, 164, 96), "norm": (232, 206, 96), "ff": (120, 170, 230),
    "linear": (170, 150, 214), "softmax": (130, 190, 120),
    "dot_r": (236, 110, 110), "dot_y": (240, 200, 100), "dot_g": (120, 200, 130), "bulb": (255, 232, 168),
    "idea": (255, 220, 90), "lit": (250, 206, 120), "lit_dim": (190, 144, 96), "star": (220, 224, 255),
    "glint": (76, 84, 136), "moon": (244, 236, 200), "moon_dk": (216, 206, 172), "zzz": (200, 205, 235),
    "warm": (255, 214, 160),
}
SKY = {   # top, middle, bottom of the sky, far buildings, near buildings
    "day": ((120, 182, 236), (152, 204, 242), (196, 228, 246), (156, 176, 204), (126, 148, 180)),
    "sunset": ((96, 96, 168), (226, 132, 132), (252, 192, 124), (128, 100, 134), (88, 72, 106)),
    "night": ((22, 28, 62), (32, 40, 84), (54, 58, 108), (38, 42, 82), (27, 29, 56)),
    "dawn": ((70, 80, 150), (206, 150, 176), (252, 206, 160), (112, 106, 142), (80, 76, 112)),
}
PAINT = {"sky1": (24, 30, 70), "sky2": (40, 48, 100), "sky3": (74, 70, 128), "b1": (30, 32, 62), "b2": (42, 44, 80)}
STARS = [(13, 9), (20, 14), (27, 9), (16, 18), (41, 16), (12, 24), (30, 16), (23, 9), (38, 9), (56, 19), (45, 21), (55, 8)]
FAR = [(10, 24), (15, 27), (20, 22), (26, 26), (31, 23), (37, 25), (42, 21), (48, 24), (53, 26)]
NEAR = [(10, 30, 6), (17, 28, 5), (23, 31, 7), (31, 29, 5), (37, 30, 6), (44, 28, 5), (50, 31, 6), (56, 29, 4)]
DISC = [".###.", "#####", "#####", "#####", ".###."]
QUESTION = [".##.", "#..#", "...#", "..#.", "....", "..#."]
BULB = [".###.", "#####", "#####", ".###."]
ZED = ["####", "..#.", ".#..", "####"]
# the Transformer figure from "Attention Is All You Need": (x0, x1, rows bottom-up of (y, block colour or "arrow"))
TRANSFORMER = [
    (107, 112, [(35, "emb"), (34, "arrow"), (33, "attn"), (32, "norm"), (31, "ff"), (30, "norm")]),
    (117, 122, [(35, "emb"), (34, "arrow"), (33, "attn"), (32, "norm"), (31, "attn"), (30, "norm"), (29, "ff"),
                (28, "norm"), (27, "arrow"), (26, "linear"), (25, "softmax")]),
]
NX_BOXES = [(106, 113, 29, 34), (116, 123, 27, 34)]
GLASS = (10, 7, 59, 34)
ART = (133, 3, 187, 22)                               # painting frame: x0, y0, x1, y1 (inner canvas is one unit in)


# ---------- contribution data ----------

def fetch(user: str) -> str:
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "profile-room"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse(html: str) -> list[dict]:
    """Weeks in calendar order: {"count": contributions, "active": days with any}."""
    counts = {}
    for target, text in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*([\d,]+) contributions?", unescape(text))
        counts[target] = int(m.group(1).replace(",", "")) if m else 0
    weeks = defaultdict(lambda: {"count": 0, "active": 0})
    for td in re.findall(r"<td[^>]*data-date[^>]*>", html):
        ident = re.search(r'id="(contribution-day-component-(\d+)-(\d+))"', td)
        if not ident:
            continue
        n = counts.get(ident.group(1), 0)
        week = weeks[int(ident.group(3))]
        week["count"] += n
        week["active"] += 1 if n else 0
    return [weeks[k] for k in sorted(weeks)]


# ---------- colour ----------

def mix(a: tuple, b: tuple, s: float) -> tuple:
    return tuple(round(x + (y - x) * s) for x, y in zip(a, b))


def night(c: tuple) -> tuple:
    return (round(c[0] * 0.22 + 6), round(c[1] * 0.24 + 8), round(c[2] * 0.36 + 26))


def phase(t: int) -> tuple[tuple, float]:
    """Sky colours and darkness (0 day, 1 night) for frame t: day, sunset, night, dawn, back to day."""
    def blend(a: str, b: str, s: float) -> tuple:
        return tuple(mix(x, y, s) for x, y in zip(SKY[a], SKY[b]))
    if t < 24:
        return SKY["day"], 0.0
    if t < 32:
        s = (t - 23) / 8
        return blend("day", "sunset", s), 0.45 * s
    if t < 38:
        s = (t - 31) / 6
        return blend("sunset", "night", s), 0.45 + 0.55 * s
    if t < 64:
        return SKY["night"], 1.0
    if t < 72:
        s = (t - 63) / 8
        return blend("night", "dawn", s), 1 - 0.55 * s
    s = (t - 71) / 8
    return blend("dawn", "day", s), 0.45 * (1 - s)


# ---------- drawing ----------

def scene(t: int, weeks: list[dict]) -> Image.Image:
    sky, dark = phase(t)
    lamp_on = dark > 0.5
    reading = 28 <= t < 56
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)

    def c(key: str, k: float = 1.0) -> tuple:
        """A surface colour at this hour; k < 1 for things lit by the screen or the lamp."""
        return mix(DAY[key], night(DAY[key]), dark * k)

    def r(x0: int, y0: int, x1: int, y1: int, colour: tuple) -> None:
        d.rectangle([x0, y0, x1, y1], fill=colour)

    def px(x: int, y: int, colour: tuple) -> None:
        d.point([x, y], fill=colour)

    def glyph(rows: list[str], x: int, y: int, colour: tuple, clip: tuple | None = None) -> None:
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == "#" and (clip is None or (clip[0] <= x + dx <= clip[2] and clip[1] <= y + dy <= clip[3])):
                    px(x + dx, y + dy, colour)

    # room shell
    r(0, 0, W - 1, 47, c("wall")); r(0, 48, W - 1, 55, c("wainscot")); r(0, 48, W - 1, 48, c("trim"))
    r(0, 56, W - 1, 56, c("base")); r(0, 57, W - 1, H - 1, c("floor"))
    for x in range(4, W, 14):
        r(x, 59, x + 7, 59, c("floor_ln"))
    for x in range(11, W, 14):
        r(x, 62, x + 7, 62, c("floor_ln"))
    if dark < 0.45:                                    # sunlight from the window on the floor
        s = (0.45 - dark) / 0.45
        for y in range(57, H):
            x0 = 16 + (y - 57) * 3
            r(x0, y, x0 + 30, y, mix(c("floor"), EMIT["warm"], 0.3 * s))
    if lamp_on:                                        # lamp light on the wall
        g1, g2 = mix(c("wall"), EMIT["warm"], 0.32), mix(c("wall"), EMIT["warm"], 0.16)
        for y in range(33, 42):
            half = 3 + (y - 33) * 0.7
            for x in range(int(156.5 - half) - 3, int(156.5 + half) + 4):
                off = abs(x - 156.5) - half
                if off <= 0:
                    px(x, y, g1 if (x + y) % 2 == 0 else g2)
                elif off <= 3 and (x + y) % 4 == 0:
                    px(x, y, g2)

    # window: sky, sun or moon, stars, skyline, glints, frame
    gx0, gy0, gx1, gy1 = GLASS
    for y in range(gy0, gy1 + 1):
        r(gx0, y, gx1, y, sky[0] if y < 14 else sky[1] if y < 24 else sky[2])
        if y in (14, 24):
            for x in range(gx0 + (y % 2), gx1 + 1, 2):
                px(x, y, sky[0] if y == 14 else sky[1])
    span = (t - 66) % FRAMES
    if span <= 47:                                     # the sun rises at dawn and sets at sunset
        p = span / 47
        height = math.sin(math.pi * p)
        sx, sy = round(gx0 + 2 + p * (gx1 - gx0 - 8)), round(gy1 - 4 - height * (gy1 - gy0 - 10))
        glyph(DISC, sx, sy, mix((255, 160, 90), (255, 240, 170), min(1.0, height * 1.6)), GLASS)
    if 30 <= t <= 70:                                  # the moon by night
        p = (t - 30) / 40
        mx, my = round(gx0 + 2 + p * (gx1 - gx0 - 8)), round(gy1 - 6 - math.sin(math.pi * p) * (gy1 - gy0 - 12))
        glyph(DISC, mx, my, EMIT["moon"], GLASS)
        for dx, dy in ((1, 2), (3, 3), (2, 1)):
            if gx0 <= mx + dx <= gx1 and gy0 <= my + dy <= gy1:
                px(mx + dx, my + dy, EMIT["moon_dk"])
    if dark > 0.75:
        fade = (dark - 0.75) / 0.25
        for i, (x, y) in enumerate(STARS):
            if (t + i * 5) % 8 < 6:
                px(x, y, mix(sky[0], EMIT["star"], fade))
        if 44 <= t <= 51:
            hx, hy = 44 - 4 * (t - 44), 8 + (3 * (t - 44)) // 2
            for k in range(8):
                x, y = hx + k, hy - (k * 3) // 8
                if gx0 <= x <= gx1 and gy0 <= y <= gy1:
                    px(x, y, EMIT["star"] if k < 3 else EMIT["glint"])
    for x, top in FAR:
        r(x, top, min(x + 4, gx1), gy1, sky[3])
    for i, (x, top, w) in enumerate(NEAR):
        r(x, top, min(x + w - 1, gx1), gy1, sky[4])
        for wy in range(top + 2, gy1, 2):
            for wx in range(x + 1, min(x + w - 1, gx1), 2):
                on = (wx * 7 + wy * 3 + i) % 5
                if dark > 0.5 and (on < 2 or (on == 2 and (t // 4 + wx) % 3 == 0)):
                    px(wx, wy, EMIT["lit"] if on == 0 else EMIT["lit_dim"])
                elif dark <= 0.5 and on < 2:
                    px(wx, wy, mix(sky[4], (255, 255, 255), 0.2))
    glint = mix((255, 255, 255), EMIT["glint"], dark)
    for x, y in [(12, 31), (13, 30), (14, 29), (38, 13), (39, 12)]:
        px(x, y, mix(sky[1], glint, 0.6))
    r(34, gy0, 35, gy1, c("frame")); r(gx0, 20, gx1, 20, c("frame"))
    r(8, 5, 61, 6, c("frame")); r(8, 35, 61, 36, c("frame")); r(8, 5, 9, 36, c("frame")); r(60, 5, 61, 36, c("frame"))
    r(6, 37, 63, 38, c("frame")); r(6, 39, 63, 39, c("frame_dk"))

    # curtain, plant on the sill
    r(0, 2, 62, 2, c("rod"))
    for x in range(0, 6):
        r(x, 3, x, 44, c("curtain" if x % 2 == 0 else "curtain_dk"))
    r(0, 45, 5, 45, c("curtain_dk"))
    r(13, 33, 17, 36, c("pot"))
    for x, y, k in [(15, 27, "plant"), (15, 28, "plant"), (15, 29, "plant"), (15, 30, "plant_dk"), (15, 31, "plant_dk"),
                    (15, 32, "plant_dk"), (13, 29, "plant"), (14, 30, "plant"), (12, 28, "plant"), (17, 28, "plant"),
                    (16, 29, "plant"), (18, 27, "plant"), (14, 31, "plant_dk"), (16, 31, "plant_dk")]:
        px(x, y, c(k))

    # note board
    r(64, 4, 85, 17, c("board_edge")); r(65, 5, 84, 16, c("cork"))
    for x0, y0, k in [(66, 6, "note_y"), (72, 7, "note_p"), (78, 6, "note_m"), (68, 11, "note_b")]:
        r(x0, y0, x0 + 4, y0 + 4, c(k)); px(x0 + 2, y0, c("pin")); r(x0 + 1, y0 + 2, x0 + 3, y0 + 2, c("note_ln"))
    flutter = (t // 3) % 4 == 0
    r(75, 11 + flutter, 79, 15, c("note_y")); px(77, 11 + flutter, c("pin"))

    # clock, spinning like a time-lapse
    cx, cy = 99, 9
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=c("rim")); d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=c("clock"))
    dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
    hx, hy = dirs[(t // 10) % 8]
    mx_, my_ = dirs[(t // 2) % 8]
    d.line([cx, cy, cx + 2 * hx, cy + 2 * hy], fill=c("hand"))
    d.line([cx, cy, cx + 3 * mx_, cy + 3 * my_], fill=c("pin"))

    # the painting: last year on GitHub as a city at night
    x0, y0, x1, y1 = ART
    k = 0.45                                           # the painting stays readable at night
    r(x0, y0, x1, y1, c("gold", k)); r(x0 + 1, y1, x1, y1, c("gold_dk", k)); r(x1, y0 + 1, x1, y1, c("gold_dk", k))
    ix0, iy0, ix1, iy1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
    for y in range(iy0, iy1 + 1):
        band = "sky1" if y < iy0 + 6 else "sky2" if y < iy0 + 12 else "sky3"
        r(ix0, y, ix1, y, mix(PAINT[band], night(PAINT[band]), dark * k))
    for x, y in [(ix0 + 4, iy0 + 2), (ix0 + 11, iy0 + 5), (ix0 + 19, iy0 + 1), (ix0 + 27, iy0 + 4), (ix0 + 35, iy0 + 2),
                 (ix0 + 43, iy0 + 6), (ix0 + 8, iy0 + 8)]:
        px(x, y, EMIT["star"])
    r(ix1 - 4, iy0 + 1, ix1 - 3, iy0 + 2, EMIT["moon"])
    cols = weeks[-(ix1 - ix0 + 1):]
    peak = max((w["count"] for w in cols), default=0) or 1
    for i, week in enumerate(cols):
        x = ix0 + i
        h = 1 + round((iy1 - iy0 - 3) * math.sqrt(week["count"] / peak)) if week["count"] else 1
        r(x, iy1 - h + 1, x, iy1, mix(PAINT["b1" if i % 2 else "b2"], night(PAINT["b1"]), dark * k))
        for j, y in enumerate(range(iy1 - 1, iy1 - h, -2)):
            if j < week["active"]:
                px(x, y, EMIT["lit"] if week["count"] >= peak * 0.25 else EMIT["lit_dim"])

    # desk, drawer
    r(66, 42, 176, 43, c("desk")); r(66, 44, 176, 44, c("desk_dk"))
    r(80, 45, 81, 55, c("desk_dk")); r(172, 45, 173, 55, c("desk_dk")); r(158, 45, 171, 50, c("desk")); r(162, 47, 167, 47, c("desk_dk"))
    if lamp_on:
        r(146, 42, 168, 42, mix(c("desk"), EMIT["warm"], 0.35)); r(150, 43, 164, 43, mix(c("desk"), EMIT["warm"], 0.25))

    # books on the floor with the rubber duck, the bin of drafts
    r(20, 52, 34, 56, c("book2")); r(20, 54, 34, 54, c("paper")); r(22, 49, 33, 51, c("book3")); r(22, 50, 33, 50, c("paper"))
    r(21, 46, 31, 48, c("book1")); r(21, 47, 31, 47, c("paper"))
    r(24, 42, 28, 45, c("duck")); r(27, 40, 29, 42, c("duck")); px(30, 41, c("beak")); px(28, 41, c("eye")); px(24, 42, c("duck"))
    r(58, 49, 65, 49, c("bin")); r(59, 50, 64, 56, c("bin_dk")); r(59, 50, 59, 56, c("bin"))
    for x, y in [(60, 48), (61, 47), (61, 48), (63, 48), (64, 47), (68, 55), (69, 55), (68, 56), (69, 56)]:
        px(x, y, c("paper"))

    # chair and the developer (lit by the screen, so they darken less)
    s = 0.6
    r(71, 30, 73, 49, c("chair", s)); r(72, 48, 84, 49, c("chair", s)); r(77, 50, 78, 55, c("chair_dk", s)); r(73, 56, 83, 56, c("chair_dk", s))
    r(78, 45, 92, 47, c("pants", s)); r(90, 48, 92, 55, c("pants", s)); r(90, 56, 95, 56, c("shoe", s))
    r(74, 33, 84, 47, c("hood", s)); r(73, 30, 76, 35, c("hood_dk", s)); r(78, 31, 80, 32, c("skin_dk", s))
    r(75, 20, 85, 31, c("skin", s)); r(74, 18, 85, 22, c("hair", s)); r(74, 18, 76, 28, c("hair", s)); px(77, 23, c("hair", s))
    if t % 20 == 13:
        r(82, 26, 83, 26, c("eye"))
    else:
        r(82, 25, 83, 26, c("eye"))
    r(84, 29, 85, 29, c("skin_dk", s)); px(85, 27, c("skin_dk", s))
    r(82, 40, 94, 41, c("key", s)); r(82, 40, 94, 40, c("key_hi", s))
    ink = mix((70, 70, 96), (230, 232, 245), dark)
    if reading:
        r(79, 35, 83, 40, c("hood_dk", s)); r(83, 33, 87, 36, c("hood_dk", s))
        r(87, 21, 95, 33, c("paper", s))
        r(88, 22, 94, 22, c("print_ink", s)); r(89, 23, 93, 23, c("paper_ln", s))
        for x0, x1, rows in ((88, 90, ["emb", "attn", "norm", "ff"]), (92, 94, ["emb", "attn", "attn", "ff", "linear", "softmax"])):
            for j, k in enumerate(rows):
                r(x0, 31 - j, x1, 31 - j, mix(EMIT[k], night(EMIT[k]), dark * s))
        r(86, 31, 88, 33, c("skin", s))
        if 32 <= t <= 39:
            px(85, 17, ink); px(86, 16, ink); glyph(QUESTION, 87, 9, ink)
        elif t >= 40:
            glyph(BULB, 86, 7, EMIT["idea"]); r(87, 11, 89, 12, c("lamp"))
            if t % 2 == 0:
                for x, y in [(85, 6), (91, 6), (84, 9), (92, 9), (88, 5)]:
                    px(x, y, EMIT["idea"])
    else:
        r(79, 35, 83, 41, c("hood_dk", s)); r(83, 39, 87, 41, c("hood_dk", s))
        up = (t // 2) % 2
        r(87, 38 - up, 89, 39 - up, c("skin", s)); r(91, 38 - (1 - up), 93, 39 - (1 - up), c("skin", s))

    # monitor: a PDF viewer open on "Attention Is All You Need", with the Transformer figure; a check once the idea lands
    r(100, 16, 132, 37, c("mon")); r(102, 18, 130, 35, EMIT["screen"]); r(114, 38, 117, 40, c("mon")); r(109, 41, 122, 41, c("mon"))
    px(104, 19, EMIT["dot_r"]); px(106, 19, EMIT["dot_y"]); px(108, 19, EMIT["dot_g"]); r(112, 19, 120, 19, EMIT["axis"])
    r(104, 21, 128, 35, EMIT["page"])
    r(108, 22, 124, 22, EMIT["ink"]); r(111, 23, 121, 23, EMIT["ink_lt"])          # title and authors
    for x0, x1, y0, y1 in NX_BOXES:                                                 # the "N x" boxes
        r(x0, y0, x0, y1, EMIT["nx"]); r(x1, y0, x1, y1, EMIT["nx"])
        r(x0, y0, x1, y0, EMIT["nx"]); r(x0, y1, x1, y1, EMIT["nx"])
        px(x0, y0, EMIT["page"]); px(x1, y0, EMIT["page"]); px(x0, y1, EMIT["page"]); px(x1, y1, EMIT["page"])
    for x0, x1, rows in TRANSFORMER:                                                # encoder and decoder stacks
        for y, colour in rows:
            if colour == "arrow":
                px((x0 + x1) // 2, y, EMIT["ink_lt"])
            else:
                r(x0, y, x1, y, EMIT[colour])
    r(113, 31, 116, 31, EMIT["ink_lt"])                                             # encoder output into the decoder
    if t >= 56:
        for x, y in [(125, 23), (126, 24), (127, 23), (128, 22)]:
            px(x, y, EMIT["ok"])

    # papers, coffee, lamp
    r(136, 40, 147, 41, c("paper")); r(136, 39, 147, 39, c("paper_ln")); r(137, 37, 146, 38, c("paper"))
    r(137, 36, 146, 36, c("paper_ln")); r(138, 34, 145, 35, c("paper")); px(141, 33, c("lamp")); px(142, 33, c("lamp"))
    r(150, 37, 153, 41, c("mug")); px(154, 38, c("mug")); px(154, 39, c("mug"))
    for j in range(3):
        px(151 + (j % 2) + ((t + j) // 2) % 2, 35 - ((t + j * 3) % 8), c("steam", 0.5))
    r(158, 40, 164, 41, c("lamp")); r(163, 30, 163, 39, c("lamp")); px(162, 29, c("lamp")); px(161, 28, c("lamp")); px(160, 28, c("lamp"))
    r(155, 28, 159, 28, c("shade_dk")); r(153, 29, 160, 31, c("shade")); r(154, 32, 159, 32, EMIT["bulb"] if lamp_on else c("bulb_off"))

    # the cat: awake by day, asleep at night
    r(176, 53, 191, 56, c("cat_bed")); r(176, 56, 191, 56, c("cat_bed_dk")); r(176, 52, 177, 53, c("cat_bed_dk")); r(190, 52, 191, 53, c("cat_bed_dk"))
    breathe = (t // 8) % 2 if lamp_on else 0
    r(178, 49 + breathe, 187, 53, c("cat")); r(179, 52, 186, 53, c("cat_dk"))
    r(185, 47 + breathe, 190, 52, c("cat")); px(185, 46 + breathe, c("cat")); px(189, 46 + breathe, c("cat"))
    if lamp_on:
        r(187, 50 + breathe, 188, 50 + breathe, c("eye"))
        for j in range(3):
            ph = (t + 5 * j) % 16
            if ph < 12:
                glyph(ZED, 185 + (j % 2) * 2 - ph // 6, 44 - ph // 2, EMIT["zzz"])
        r(178, 52, 181, 52, c("cat_dk")); px(177, 51, c("cat_dk"))
    else:
        px(187, 49, c("eye")); px(189, 49, c("eye"))
        tip = (t // 3) % 2
        r(176, 51, 178, 51, c("cat_dk")); px(176, 50 - tip, c("cat_dk"))
    return im


FONT = {  # 3 x 5 pixel letters for the plaque
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."], "E": ["###", "#..", "##.", "#..", "###"],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "M": ["#.#", "###", "###", "#.#", "#.#"], "N": ["##.", "#.#", "#.#", "#.#", "#.#"], "O": ["###", "#.#", "#.#", "#.#", "###"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "T": ["###", ".#.", ".#.", ".#.", ".#."], "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], " ": ["...", "...", "...", "...", "..."],
}
PLAQUE = "MY YEAR ON GITHUB"


def plaque(img: Image.Image, dark: float) -> None:
    """A small brass plaque under the painting, engraved in a fine pixel font (2 px per font pixel on the final image)."""
    d = ImageDraw.Draw(img)
    cell, pad = 2, 6
    text_w = (len(PLAQUE) * 4 - 1) * cell
    w, h = text_w + 2 * pad, 5 * cell + 6
    x0 = (ART[0] + ART[2] + 1) * SCALE // 2 - w // 2
    y0 = (ART[3] + 1) * SCALE + 3
    tone = lambda c: mix(c, night(c), dark * 0.45)                                  # noqa: E731
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=tone(DAY["gold"]))
    d.rectangle([x0, y0 + h - 2, x0 + w - 1, y0 + h - 1], fill=tone(DAY["gold_dk"]))
    ink = tone((96, 66, 32))
    x = x0 + pad
    for ch in PLAQUE:
        for ry, row in enumerate(FONT[ch]):
            for rx, v in enumerate(row):
                if v == "#":
                    px, py = x + rx * cell, y0 + 3 + ry * cell
                    d.rectangle([px, py, px + cell - 1, py + cell - 1], fill=ink)
        x += 4 * cell


def to_palette(im: Image.Image, outside: Image.Image) -> Image.Image:
    """Exact palette for one frame (pixel art has few colours), with index 0 kept for the transparent corners."""
    colours = [KEY] + sorted({col for _, col in im.getcolors(maxcolors=im.width * im.height)} - {KEY})
    flat = [v for col in colours for v in col]
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat + [0] * (768 - len(flat)))
    q = im.quantize(palette=pal, dither=Image.Dither.NONE)
    q.paste(0, mask=outside)
    return q


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else "hugebenevolence"
    path = sys.argv[2] if len(sys.argv) > 2 else "dist/room.gif"
    html = open(sys.argv[3], encoding="utf-8").read() if len(sys.argv) > 3 else fetch(user)
    weeks = parse(html)
    if not weeks:
        sys.exit("no contribution data found")
    inside = Image.new("L", (W, H), 0)
    ImageDraw.Draw(inside).rounded_rectangle([0, 0, W - 1, H - 1], radius=4, fill=255)
    edge = Image.new("L", (W, H), 0)
    ImageDraw.Draw(edge).rounded_rectangle([0, 0, W - 1, H - 1], radius=4, outline=255)
    outside = inside.point(lambda a: 255 - a).resize((W * SCALE, H * SCALE), Image.NEAREST)
    frames = []
    for t in range(FRAMES):
        im = scene(t, weeks)
        im.paste(EDGE, mask=edge)
        big = im.resize((W * SCALE, H * SCALE), Image.NEAREST)
        plaque(big, phase(t)[1])
        frames.append(to_palette(big, outside))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=MS, loop=0, transparency=0, disposal=1,
                   optimize=False)
    print(f"wrote {path} ({os.path.getsize(path) // 1024} KB, {len(weeks)} weeks, "
          f"{sum(w['count'] for w in weeks)} contributions)")


if __name__ == "__main__":
    main()
