"""Pixel-art hero for the profile README (assets/room.gif).

A night room: the developer trains a model and watches the loss fall, picks up a paper, gets stuck ("?"), gets the idea (a
light bulb), goes back to the keyboard and the run passes. Around them: a window with the city, the moon and a shooting
star, a ticking clock, a note board, a bin of crumpled drafts, a desk lamp, a stack of papers and a cat asleep on the floor.

The scene is drawn on a 192 x 64 grid and scaled x4 with nearest-neighbour (768 x 256 px), so the pixels stay sharp. Every
animation has a period that divides the 48 frames, so the loop has no jump. Needs Pillow:

    python3 assets/build_room.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, SCALE, FRAMES, MS = 192, 64, 4, 48, 100

C = {
    "edge": (24, 26, 44), "wall": (46, 50, 82), "wall_low": (40, 43, 72), "glow": (104, 88, 96), "glow2": (66, 62, 90),
    "floor": (32, 34, 56), "board": (40, 43, 70),
    "frame": (118, 92, 84), "frame_dk": (90, 68, 64),
    "sky1": (22, 28, 62), "sky2": (32, 40, 84), "sky3": (54, 58, 108), "glint": (76, 84, 136),
    "moon": (244, 236, 200), "moon_dk": (216, 206, 172), "star": (220, 224, 255), "far": (38, 42, 82), "near": (27, 29, 56),
    "lit": (250, 206, 120), "lit_dim": (186, 140, 92),
    "curtain": (124, 92, 120), "curtain_dk": (98, 70, 98), "rod": (24, 26, 44),
    "desk": (128, 90, 70), "desk_dk": (96, 66, 52), "desk_lit": (170, 122, 88),
    "shelf": (98, 70, 58), "book1": (170, 92, 82), "book2": (92, 132, 172), "book3": (204, 172, 104), "book4": (112, 152, 112),
    "book5": (150, 112, 162),
    "cork": (150, 112, 80), "note_y": (240, 212, 112), "note_p": (236, 150, 170), "note_m": (140, 210, 170),
    "note_b": (130, 180, 240), "pin": (220, 80, 80), "clock": (230, 226, 210), "hand": (40, 40, 56),
    "lamp": (150, 156, 186), "shade": (214, 124, 92), "shade_dk": (176, 98, 76), "bulb": (255, 232, 168),
    "idea": (255, 220, 90), "bubble": (230, 232, 245),
    "mon": (30, 32, 48), "screen": (18, 22, 38), "axis": (84, 92, 128), "loss": (236, 140, 150), "ok": (120, 210, 140),
    "c_text": (196, 202, 220), "dot_r": (236, 110, 110), "dot_y": (240, 200, 100), "dot_g": (120, 200, 130),
    "key": (72, 76, 108), "key_hi": (104, 108, 142), "mug": (222, 222, 232), "steam": (150, 156, 190),
    "paper": (238, 236, 228), "paper_ln": (168, 170, 186), "fig": (110, 170, 255),
    "skin": (236, 196, 160), "skin_dk": (206, 160, 130), "hair": (36, 28, 32), "eye": (30, 30, 40),
    "hood": (78, 122, 150), "hood_dk": (60, 96, 124), "pants": (48, 52, 78), "shoe": (222, 222, 232),
    "chair": (64, 66, 96), "chair_dk": (50, 52, 80), "bin": (84, 92, 128), "bin_dk": (66, 72, 104),
    "plant": (96, 166, 104), "plant_dk": (70, 124, 82), "pot": (176, 112, 92),
    "cat": (168, 168, 186), "cat_dk": (118, 118, 140), "cat_bed": (150, 90, 112), "cat_bed_dk": (118, 68, 90),
    "zzz": (200, 205, 235),
}
STARS = [(13, 9), (20, 14), (27, 9), (16, 18), (41, 16), (12, 24), (30, 16), (23, 9), (38, 9), (56, 19), (45, 21), (55, 8)]
FAR = [(10, 24), (15, 27), (20, 22), (26, 26), (31, 23), (37, 25), (42, 21), (48, 24), (53, 26)]
NEAR = [(10, 30, 6), (17, 28, 5), (23, 31, 7), (31, 29, 5), (37, 30, 6), (44, 28, 5), (50, 31, 6), (56, 29, 4)]
QUESTION = [".##.", "#..#", "...#", "..#.", "....", "..#."]
BULB = [".###.", "#####", "#####", ".###."]
ZED = ["####", "..#.", ".#..", "####"]
LOSS = [round(23 + 9 * (1 - math.exp(-i / 5)) + (1 if i in (3, 8, 13) else 0) - (1 if i in (5, 10) else 0)) for i in range(24)]


def scene(t: int) -> Image.Image:
    im = Image.new("RGB", (W, H), C["wall"])
    d = ImageDraw.Draw(im)

    def r(x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        d.rectangle([x0, y0, x1, y1], fill=C[c])

    def px(x: int, y: int, c: str) -> None:
        d.point([x, y], fill=C[c])

    def glyph(rows: list[str], x: int, y: int, c: str) -> None:
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch == "#":
                    px(x + dx, y + dy, c)

    reading = 24 <= t < 36

    # room
    r(0, 48, W - 1, 55, "wall_low"); r(0, 56, W - 1, 56, "edge"); r(0, 57, W - 1, H - 1, "floor")
    for x in range(4, W, 14):
        r(x, 59, x + 7, 59, "board")
    for x in range(11, W, 14):
        r(x, 62, x + 7, 62, "board")

    # lamp light, a cone from the shade down to the desk
    for y in range(27, 42):
        half = 3 + (y - 27) * 0.6
        for x in range(int(156.5 - half) - 3, int(156.5 + half) + 4):
            off = abs(x - 156.5) - half
            if off <= 0:
                px(x, y, "glow" if (x + y) % 2 == 0 else "glow2")
            elif off <= 3 and (x + y) % 4 == 0:
                px(x, y, "glow2")

    # window: sky, moon, stars, shooting star, skyline, glints, mullions, frame, sill
    gx0, gy0, gx1, gy1 = 10, 7, 59, 34
    for y in range(gy0, gy1 + 1):
        r(gx0, y, gx1, y, "sky1" if y < 14 else "sky2" if y < 24 else "sky3")
        if y in (14, 24):
            for x in range(gx0 + (y % 2), gx1 + 1, 2):
                px(x, y, "sky1" if y == 14 else "sky2")
    r(49, 9, 51, 9, "moon"); r(48, 10, 52, 12, "moon"); r(49, 13, 51, 13, "moon")
    px(49, 11, "moon_dk"); px(51, 12, "moon_dk"); px(50, 10, "moon_dk")
    for i, (x, y) in enumerate(STARS):
        phase = (t + i * 5) % 8
        if phase < 6:
            px(x, y, "star")
        if phase == 2 and i % 4 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px(x + dx, y + dy, "glint")
    if 6 <= t <= 13:
        p = t - 6
        hx, hy = 44 - 4 * p, 8 + (3 * p) // 2
        for k in range(8):
            x, y = hx + k, hy - (k * 3) // 8
            if gx0 <= x <= gx1 and gy0 <= y <= gy1:
                px(x, y, "star" if k < 3 else "glint")
    for x, top in FAR:
        r(x, top, min(x + 4, gx1), gy1, "far")
    for i, (x, top, w) in enumerate(NEAR):
        r(x, top, min(x + w - 1, gx1), gy1, "near")
        for wy in range(top + 2, gy1, 2):
            for wx in range(x + 1, min(x + w - 1, gx1), 2):
                on = (wx * 7 + wy * 3 + i) % 5
                if on < 2 or (on == 2 and (t // 4 + wx) % 3 == 0):
                    px(wx, wy, "lit" if on == 0 else "lit_dim")
    for x, y in [(12, 31), (13, 30), (14, 29), (38, 13), (39, 12)]:
        px(x, y, "glint")
    r(34, gy0, 35, gy1, "frame"); r(gx0, 20, gx1, 20, "frame")
    r(8, 5, 61, 6, "frame"); r(8, 35, 61, 36, "frame"); r(8, 5, 9, 36, "frame"); r(60, 5, 61, 36, "frame")
    r(6, 37, 63, 38, "frame"); r(6, 39, 63, 39, "frame_dk")

    # curtain and rod
    r(0, 2, 62, 2, "rod")
    for x in range(0, 6):
        r(x, 3, x, 44, "curtain" if x % 2 == 0 else "curtain_dk")
    r(0, 45, 5, 45, "curtain_dk")

    # plant on the sill
    r(13, 33, 17, 36, "pot")
    for x, y, c in [(15, 27, "plant"), (15, 28, "plant"), (15, 29, "plant"), (15, 30, "plant_dk"), (15, 31, "plant_dk"),
                    (15, 32, "plant_dk"), (13, 29, "plant"), (14, 30, "plant"), (12, 28, "plant"), (17, 28, "plant"),
                    (16, 29, "plant"), (18, 27, "plant"), (14, 31, "plant_dk"), (16, 31, "plant_dk")]:
        px(x, y, c)

    # note board
    r(64, 4, 85, 17, "edge"); r(65, 5, 84, 16, "cork")
    for x0, y0, c in [(66, 6, "note_y"), (72, 7, "note_p"), (78, 6, "note_m"), (68, 11, "note_b")]:
        r(x0, y0, x0 + 4, y0 + 4, c); px(x0 + 2, y0, "pin")
        r(x0 + 1, y0 + 2, x0 + 3, y0 + 2, "paper_ln")
    flutter = (t // 3) % 4 == 0
    r(75, 11 + flutter, 79, 15, "note_y"); px(77, 11 + flutter, "pin")

    # clock with a minute hand that goes round once per loop
    cx, cy = 99, 9
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=C["edge"]); d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=C["clock"])
    d.line([cx, cy, cx - 2, cy - 1], fill=C["hand"])
    mx, my = [(0, -3), (2, -2), (3, 0), (2, 2), (0, 3), (-2, 2), (-3, 0), (-2, -2)][(t // 6) % 8]
    d.line([cx, cy, cx + mx, cy + my], fill=C["pin"])

    # bookshelf
    r(140, 13, 182, 13, "shelf"); r(140, 14, 182, 14, "desk_dk")
    x = 141
    for i, (w, h) in enumerate([(2, 7), (3, 6), (2, 8), (2, 5), (3, 7), (2, 6), (4, 3), (2, 7), (3, 8), (2, 6), (3, 5),
                                (2, 7)]):
        r(x, 13 - h, x + w - 1, 12, f"book{i % 5 + 1}")
        x += w + (1 if i in (3, 6, 9) else 0)
    r(x + 2, 9, x + 4, 12, "pot"); px(x + 3, 7, "plant"); px(x + 2, 8, "plant"); px(x + 4, 8, "plant"); px(x + 3, 8, "plant_dk")

    # desk, its far leg and drawer, light from the lamp
    r(66, 42, 176, 43, "desk"); r(66, 44, 176, 44, "desk_dk")
    r(80, 45, 81, 55, "desk_dk"); r(172, 45, 173, 55, "desk_dk"); r(158, 45, 171, 50, "desk"); r(162, 47, 167, 47, "desk_dk")
    r(146, 42, 168, 42, "desk_lit"); r(150, 43, 164, 43, "desk_lit")

    # books piled on the floor, with the rubber duck that gets the bugs explained to it
    r(20, 52, 34, 56, "book2"); r(20, 54, 34, 54, "paper"); r(22, 49, 33, 51, "book3"); r(22, 50, 33, 50, "paper")
    r(21, 46, 31, 48, "book1"); r(21, 47, 31, 47, "paper")
    r(24, 42, 28, 45, "idea"); r(27, 40, 29, 42, "idea"); px(30, 41, "shade"); px(28, 41, "eye"); px(24, 42, "idea")

    # bin of crumpled drafts, one that missed
    r(58, 49, 65, 49, "bin"); r(59, 50, 64, 56, "bin_dk"); r(59, 50, 59, 56, "bin")
    for x, y in [(60, 48), (61, 47), (61, 48), (63, 48), (64, 47), (68, 55), (69, 55), (68, 56), (69, 56)]:
        px(x, y, "paper")

    # chair
    r(71, 30, 73, 49, "chair"); r(72, 48, 84, 49, "chair"); r(77, 50, 78, 55, "chair_dk"); r(73, 56, 83, 56, "chair_dk")

    # the developer
    r(78, 45, 92, 47, "pants"); r(90, 48, 92, 55, "pants"); r(90, 56, 95, 56, "shoe")
    r(74, 33, 84, 47, "hood"); r(73, 30, 76, 35, "hood_dk")
    r(78, 31, 80, 32, "skin_dk")
    r(75, 20, 85, 31, "skin"); r(74, 18, 85, 22, "hair"); r(74, 18, 76, 28, "hair"); px(77, 23, "hair")
    if t % 16 == 11:
        r(82, 26, 83, 26, "eye")
    else:
        r(82, 25, 83, 26, "eye")
    r(84, 29, 85, 29, "skin_dk"); px(85, 27, "skin_dk")
    r(82, 40, 94, 41, "key"); r(82, 40, 94, 40, "key_hi")
    if reading:
        # arm raised, holding a paper with a figure on it
        r(79, 35, 83, 40, "hood_dk"); r(83, 33, 87, 36, "hood_dk")
        r(87, 21, 95, 33, "paper")
        for y, n in [(23, 7), (25, 5), (31, 6)]:
            r(88, y, 88 + n - 1, y, "paper_ln")
        r(88, 27, 91, 29, "fig"); r(93, 27, 94, 27, "paper_ln"); r(93, 29, 94, 29, "paper_ln")
        r(86, 31, 88, 33, "skin")
        if 25 <= t <= 29:
            px(85, 17, "bubble"); px(86, 16, "bubble")
            glyph(QUESTION, 87, 9, "bubble")
        elif t >= 30:
            glyph(BULB, 86, 7, "idea"); r(87, 11, 89, 12, "lamp")
            if t % 2 == 0:
                for x, y in [(85, 6), (91, 6), (84, 9), (92, 9), (88, 5)]:
                    px(x, y, "idea")
    else:
        r(79, 35, 83, 41, "hood_dk"); r(83, 39, 87, 41, "hood_dk")
        up = (t // 2) % 2
        r(87, 38 - up, 89, 39 - up, "skin"); r(91, 38 - (1 - up), 93, 39 - (1 - up), "skin")

    # monitor: a training run, the loss falling point by point, then a check once the idea lands
    r(100, 16, 132, 37, "mon"); r(102, 18, 130, 35, "screen"); r(114, 38, 117, 40, "mon"); r(109, 41, 122, 41, "mon")
    px(104, 19, "dot_r"); px(106, 19, "dot_y"); px(108, 19, "dot_g"); r(112, 19, 120, 19, "axis")
    r(104, 22, 104, 33, "axis"); r(104, 33, 128, 33, "axis")
    shown = min(24, t + 1)
    for i in range(shown):
        x, y = 105 + i, LOSS[i]
        px(x, y, "loss")
        if i:
            for yy in range(min(y, LOSS[i - 1]), max(y, LOSS[i - 1])):
                px(x, yy, "loss")
    if t < 24:
        px(105 + shown - 1, LOSS[shown - 1] - 1, "c_text")
    if t >= 36:
        for x, y in [(118, 25), (119, 26), (120, 27), (121, 26), (122, 25), (123, 24), (124, 23)]:
            px(x, y, "ok"); px(x, y + 1, "ok")

    # stack of papers, coffee, lamp
    r(136, 40, 147, 41, "paper"); r(136, 39, 147, 39, "paper_ln"); r(137, 37, 146, 38, "paper"); r(137, 36, 146, 36, "paper_ln")
    r(138, 34, 145, 35, "paper"); px(141, 33, "lamp"); px(142, 33, "lamp")
    r(150, 37, 153, 41, "mug"); px(154, 38, "mug"); px(154, 39, "mug")
    for k in range(3):
        y = 35 - ((t + k * 3) % 8)
        px(151 + (k % 2) + ((t + k) // 2) % 2, y, "steam")
    r(158, 40, 164, 41, "lamp"); r(163, 24, 163, 39, "lamp"); px(162, 23, "lamp"); px(161, 22, "lamp"); px(160, 22, "lamp")
    r(155, 21, 159, 22, "shade_dk"); r(153, 23, 160, 25, "shade"); r(154, 26, 159, 26, "bulb")

    # the cat, asleep in its bed, breathing, with z's floating up
    r(176, 53, 191, 56, "cat_bed"); r(176, 56, 191, 56, "cat_bed_dk"); r(176, 52, 177, 53, "cat_bed_dk"); r(190, 52, 191, 53, "cat_bed_dk")
    breathe = (t // 8) % 2
    r(178, 49 + breathe, 187, 53, "cat"); r(179, 52, 186, 53, "cat_dk")
    r(185, 47 + breathe, 190, 52, "cat"); px(185, 46 + breathe, "cat"); px(189, 46 + breathe, "cat")
    r(187, 50 + breathe, 188, 50 + breathe, "eye")
    r(178, 52, 181, 52, "cat_dk"); px(177, 51, "cat_dk")
    for k in range(3):
        phase = (t + 5 * k) % 16
        if phase < 12:
            glyph(ZED, 185 + (k % 2) * 2 - phase // 6, 44 - phase // 2, "zzz")
    return im


def main() -> None:
    inside = Image.new("L", (W, H), 0)
    ImageDraw.Draw(inside).rounded_rectangle([0, 0, W - 1, H - 1], radius=4, fill=255)
    edge = Image.new("L", (W, H), 0)
    ImageDraw.Draw(edge).rounded_rectangle([0, 0, W - 1, H - 1], radius=4, outline=255)
    colours = sorted(set(C.values()))
    flat = [255, 0, 255] + [v for c in colours for v in c]       # palette index 0 is the transparent corner colour
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat + [0] * (768 - len(flat)))
    frames = []
    for t in range(FRAMES):
        im = scene(t)
        im.paste(C["edge"], mask=edge)
        q = im.quantize(palette=pal, dither=Image.Dither.NONE)
        q.paste(0, mask=inside.point(lambda a: 255 - a))
        frames.append(q.resize((W * SCALE, H * SCALE), Image.NEAREST))
    path = HERE / "room.gif"
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=MS, loop=0, transparency=0, disposal=1,
                   optimize=False)
    print(f"wrote {path.relative_to(HERE.parent)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
