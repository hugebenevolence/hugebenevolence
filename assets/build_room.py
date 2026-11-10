"""Pixel-art night room for the profile README (assets/room.gif): a developer codes at a desk beside a rainy window, with
the city and the moon outside, a desk lamp, a bookshelf and a plant on the sill.

The scene is drawn on a 104 x 64 grid and scaled x4 with nearest-neighbour, so the README shows it at its native 416 x 256 px
and the pixels stay sharp. Everything that moves (rain, stars, city lights, typing, code, cursor, steam, blinking) has a
period that divides the 24 frames, so the loop has no jump. Needs Pillow:

    python3 assets/build_room.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, SCALE, FRAMES, MS = 104, 64, 4, 24, 120

C = {
    "edge": (24, 26, 44), "wall": (46, 50, 82), "wall_low": (40, 43, 72), "glow": (92, 82, 98), "glow2": (70, 66, 92),
    "floor": (32, 34, 56), "board": (40, 43, 70),
    "frame": (118, 92, 84), "frame_dk": (90, 68, 64),
    "sky1": (22, 28, 62), "sky2": (32, 40, 84), "sky3": (54, 58, 108), "glint": (76, 84, 136),
    "moon": (244, 236, 200), "star": (220, 224, 255), "far": (38, 42, 82), "near": (27, 29, 56),
    "lit": (250, 206, 120), "lit_dim": (186, 140, 92), "rain": (128, 150, 206),
    "curtain": (124, 92, 120), "curtain_dk": (98, 70, 98), "rod": (24, 26, 44),
    "desk": (128, 90, 70), "desk_dk": (96, 66, 52), "desk_lit": (170, 122, 88),
    "shelf": (98, 70, 58), "book1": (170, 92, 82), "book2": (92, 132, 172), "book3": (204, 172, 104), "book4": (112, 152, 112),
    "book5": (150, 112, 162), "poster": (210, 196, 170), "sun": (232, 150, 110), "hill": (112, 152, 112),
    "lamp": (150, 156, 186), "shade": (214, 124, 92), "shade_dk": (176, 98, 76), "bulb": (255, 232, 168),
    "moon_dk": (216, 206, 172),
    "mon": (30, 32, 48), "screen": (18, 22, 38), "c_blue": (110, 170, 255), "c_green": (120, 200, 130),
    "c_text": (196, 202, 220), "c_pink": (230, 140, 170),
    "key": (72, 76, 108), "key_hi": (104, 108, 142), "mug": (222, 222, 232), "steam": (150, 156, 190),
    "skin": (236, 196, 160), "skin_dk": (206, 160, 130), "hair": (36, 28, 32), "eye": (30, 30, 40),
    "hood": (78, 122, 150), "hood_dk": (60, 96, 124), "pants": (48, 52, 78), "shoe": (222, 222, 232),
    "chair": (64, 66, 96), "chair_dk": (50, 52, 80),
    "plant": (96, 166, 104), "plant_dk": (70, 124, 82), "pot": (176, 112, 92),
}
CODE = [(0, 9, "c_blue"), (2, 12, "c_text"), (2, 7, "c_green"), (4, 10, "c_text"), (2, 5, "c_pink"), (0, 8, "c_blue"),
        (2, 11, "c_text"), (4, 6, "c_green")]                     # (indent, length, colour); 8 lines, one step per 3 frames
STARS = [(10, 9), (17, 13), (27, 8), (13, 17), (36, 17), (9, 24), (30, 15), (20, 9)]
FAR = [(7, 24), (11, 27), (16, 22), (21, 26), (27, 23), (32, 25), (37, 21)]      # (x start, top y), buildings 5 px wide
NEAR = [(7, 30, 6), (14, 28, 5), (20, 31, 7), (28, 29, 5), (34, 30, 6)]           # (x start, top y, width)
DROPS = [(9, 0), (12, 21), (15, 9), (18, 30), (21, 14), (25, 4), (28, 25), (31, 11), (34, 33), (37, 18), (11, 27), (26, 16),
         (33, 2), (19, 23)]                                                        # (x, phase); fall 3 px a frame, period 36


def scene(t: int) -> Image.Image:
    im = Image.new("RGB", (W, H), C["wall"])
    d = ImageDraw.Draw(im)

    def r(x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        d.rectangle([x0, y0, x1, y1], fill=C[c])

    def px(x: int, y: int, c: str) -> None:
        d.point([x, y], fill=C[c])

    # room: lower wall, baseboard, floor boards
    r(0, 48, W - 1, 55, "wall_low"); r(0, 56, W - 1, 56, "edge"); r(0, 57, W - 1, H - 1, "floor")
    for x in range(4, W, 14):
        r(x, 59, x + 7, 59, "board")
    for x in range(11, W, 14):
        r(x, 62, x + 7, 62, "board")

    # lamp light: a cone from the shade down to the desk, solid in the middle and dithered at the edges
    for y in range(27, 42):
        half = 3 + (y - 27) * 0.55
        for x in range(int(94.5 - half) - 3, min(W, int(94.5 + half) + 4)):
            off = abs(x - 94.5) - half
            if off <= 0:
                px(x, y, "glow")
            elif off <= 1.5 and (x + y) % 2 == 0:
                px(x, y, "glow")
            elif off <= 3.5 and (x + y) % 2 == 0:
                px(x, y, "glow2")

    # window: sky bands with dithered seams, moon, stars, skyline, rain, glints, mullions, frame and sill
    gx0, gy0, gx1, gy1 = 7, 7, 39, 35
    for y in range(gy0, gy1 + 1):
        band = "sky1" if y < 15 else "sky2" if y < 25 else "sky3"
        r(gx0, y, gx1, y, band)
        if y in (15, 25):
            for x in range(gx0, gx1 + 1, 2):
                px(x + (y % 2), y, "sky1" if y == 15 else "sky2")
    r(30, 9, 32, 9, "moon"); r(29, 10, 33, 12, "moon"); r(30, 13, 32, 13, "moon")
    px(30, 11, "moon_dk"); px(32, 12, "moon_dk"); px(31, 10, "moon_dk")
    for i, (x, y) in enumerate(STARS):
        phase = (t + i * 5) % 8
        if phase < 6:
            px(x, y, "star")
        if phase == 2 and i % 3 == 0:
            px(x - 1, y, "glint"); px(x + 1, y, "glint"); px(x, y - 1, "glint"); px(x, y + 1, "glint")
    for x, top in FAR:
        r(x, top, min(x + 4, gx1), gy1, "far")
    for i, (x, top, w) in enumerate(NEAR):
        r(x, top, min(x + w - 1, gx1), gy1, "near")
        for wy in range(top + 2, gy1, 2):
            for wx in range(x + 1, min(x + w - 1, gx1), 2):
                on = (wx * 7 + wy * 3 + i) % 5
                if on < 2 or (on == 2 and (t // 4 + wx) % 3 == 0):
                    px(wx, wy, "lit" if on == 0 else "lit_dim")
    for x, phase in DROPS:
        y = gy0 - 3 + (phase + 3 * t) % 36
        for k in range(2):
            if gy0 <= y + k <= gy1:
                px(x - (1 if k else 0), y + k, "rain")
    for x, y in [(9, 30), (10, 29), (11, 28), (26, 12), (27, 11)]:
        px(x, y, "glint")
    r(22, gy0, 23, gy1, "frame"); r(gx0, 21, gx1, 21, "frame")
    r(5, 5, 41, 6, "frame"); r(5, 36, 41, 36, "frame"); r(5, 5, 6, 36, "frame"); r(40, 5, 41, 36, "frame")
    r(3, 37, 43, 38, "frame"); r(3, 39, 43, 39, "frame_dk")

    # curtain and rod on the left
    r(0, 2, 46, 2, "rod")
    for x in range(0, 5):
        r(x, 3, x, 44, "curtain" if x % 2 == 0 else "curtain_dk")
    r(0, 45, 4, 45, "curtain_dk")

    # plant on the sill
    r(10, 33, 14, 36, "pot")
    for x, y, c in [(12, 27, "plant"), (12, 28, "plant"), (12, 29, "plant"), (12, 30, "plant_dk"), (12, 31, "plant_dk"),
                    (12, 32, "plant_dk"), (10, 29, "plant"), (11, 30, "plant"), (9, 28, "plant"), (14, 28, "plant"),
                    (13, 29, "plant"), (15, 27, "plant"), (11, 31, "plant_dk"), (13, 31, "plant_dk")]:
        px(x, y, c)

    # poster with a sun and hills
    r(48, 5, 58, 14, "edge"); r(49, 6, 57, 13, "poster"); r(52, 7, 54, 9, "sun")
    for x in range(49, 58):
        top = 11 - (1 if 51 <= x <= 55 else 0)
        r(x, top, x, 13, "hill")

    # bookshelf over the monitor
    r(62, 13, 92, 13, "shelf"); r(62, 14, 92, 14, "desk_dk")
    x = 63
    for i, (w, h) in enumerate([(2, 7), (3, 6), (2, 8), (2, 5), (3, 7), (2, 6), (4, 3), (2, 7), (3, 8), (2, 6)]):
        r(x, 13 - h, x + w - 1, 12, f"book{i % 5 + 1}")
        x += w + (1 if i in (3, 6) else 0)
    r(x + 2, 9, x + 4, 12, "pot"); px(x + 3, 7, "plant"); px(x + 2, 8, "plant"); px(x + 4, 8, "plant"); px(x + 3, 8, "plant_dk")

    # desk (behind the person), near leg, drawer, lamp light on the top
    r(44, 42, W - 1, 43, "desk"); r(44, 44, W - 1, 44, "desk_dk")
    r(56, 45, 57, 55, "desk_dk"); r(98, 45, 99, 55, "desk_dk"); r(88, 45, 99, 50, "desk"); r(92, 47, 95, 47, "desk_dk")
    r(84, 42, W - 1, 42, "desk_lit"); r(88, 43, 101, 43, "desk_lit")

    # chair
    r(45, 30, 47, 49, "chair"); r(46, 48, 58, 49, "chair"); r(51, 50, 52, 55, "chair_dk"); r(47, 56, 57, 56, "chair_dk")

    # person facing right: legs under the desk, torso with hood, head, hair, blinking eye, arm and tapping hands
    r(52, 45, 66, 47, "pants"); r(64, 48, 66, 55, "pants"); r(64, 56, 69, 56, "shoe")
    r(48, 33, 58, 47, "hood"); r(47, 30, 50, 35, "hood_dk")
    r(52, 31, 54, 32, "skin_dk")
    r(49, 20, 59, 31, "skin"); r(48, 18, 59, 22, "hair"); r(48, 18, 50, 28, "hair"); px(51, 23, "hair")
    if t % 12 == 7:
        r(56, 26, 57, 26, "eye")
    else:
        r(56, 25, 57, 26, "eye")
    r(58, 29, 59, 29, "skin_dk"); px(59, 27, "skin_dk")
    r(53, 35, 57, 41, "hood_dk"); r(57, 39, 61, 41, "hood_dk")
    up = (t // 2) % 2
    r(56, 40, 68, 41, "key"); r(56, 40, 68, 40, "key_hi")
    r(61, 38 - up, 63, 39 - up, "skin"); r(65, 38 - (1 - up), 67, 39 - (1 - up), "skin")

    # monitor with scrolling code and a blinking cursor
    r(70, 20, 90, 37, "mon"); r(72, 22, 88, 35, "screen"); r(79, 38, 81, 40, "mon"); r(75, 41, 85, 41, "mon")
    shift = (t // 3) % len(CODE)
    for row in range(6):
        ind, length, col = CODE[(row + shift) % len(CODE)]
        y = 23 + row * 2
        r(74 + ind, y, min(74 + ind + length, 86), y, col)
    if (t // 3) % 2 == 0:
        ind, length, _ = CODE[(5 + shift) % len(CODE)]
        x = min(74 + ind + length + 2, 87)
        r(x, 32, x, 34, "c_text")

    # mug with steam, between keyboard and monitor
    r(70, 37, 73, 41, "mug"); px(74, 38, "mug"); px(74, 39, "mug")
    for k in range(3):
        y = 35 - ((t + k * 3) % 8)
        x = 71 + (k % 2) + ((t + k) // 2) % 2
        px(x, y, "steam")

    # desk lamp on the right: metal base and arm, warm shade, bright bulb
    r(96, 40, 102, 41, "lamp"); r(101, 24, 101, 39, "lamp"); px(100, 23, "lamp"); px(99, 22, "lamp"); px(98, 22, "lamp")
    r(93, 21, 97, 22, "shade_dk"); r(91, 23, 98, 25, "shade"); r(92, 26, 97, 26, "bulb")
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
