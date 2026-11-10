"""Pixel-art developer typing at a desk: assets/dev-light.gif and assets/dev-dark.gif, one per GitHub theme.

The scene is drawn on a 96 x 58 grid with a transparent background and scaled x4 with nearest-neighbour, so the README shows it
at its native 384 x 232 px and the pixels stay sharp. Needs Pillow:

    python3 assets/build_gif.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
W, H, TOP, SCALE, FRAMES, MS = 96, 58, 10, 4, 24, 110      # TOP: rows cropped off the top of the 96 x 68 drawing grid

PALETTES = {
    "light": {"ink": (36, 41, 47), "eye": (36, 41, 47), "skin": (233, 196, 160), "hair": (36, 41, 47), "shirt": (87, 96, 106), "pants": (57, 65, 74),
              "chair": (140, 149, 159), "desk": (175, 184, 193), "frame": (36, 41, 47), "screen": (246, 248, 250),
              "code": (9, 105, 218), "code2": (26, 127, 55), "key": (208, 215, 222), "mug": (87, 96, 106),
              "steam": (175, 184, 193), "plant": (26, 127, 55), "pot": (140, 149, 159)},
    "dark": {"ink": (201, 209, 217), "eye": (36, 41, 47), "skin": (226, 190, 156), "hair": (92, 72, 60), "shirt": (110, 118, 129), "pants": (72, 79, 88),
             "chair": (56, 62, 70), "desk": (88, 96, 105), "frame": (139, 148, 158), "screen": (22, 27, 34),
             "code": (88, 166, 255), "code2": (63, 185, 80), "key": (48, 54, 61), "mug": (139, 148, 158),
             "steam": (110, 118, 129), "plant": (63, 185, 80), "pot": (88, 96, 105)},
}
# Code on the screen as (indent, length, colour); the text scrolls up one line every 3 frames.
CODE = [(0, 10, "code"), (2, 14, "ink"), (2, 9, "code2"), (4, 12, "ink"), (2, 6, "code"), (0, 8, "code2"), (2, 13, "ink"),
        (4, 7, "code"), (2, 11, "ink"), (0, 5, "code2"), (2, 12, "code"), (4, 9, "ink")]


def frame(p: dict, t: int) -> Image.Image:
    im = Image.new("RGBA", (W, H + TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def r(x0: int, y0: int, x1: int, y1: int, c: str) -> None:
        d.rectangle([x0, y0, x1, y1], fill=p[c])

    # Behind the person: the near desk leg, the chair and a floor plant. The ground line is y = 66.
    r(33, 48, 34, 66, "desk")
    r(12, 28, 14, 52, "chair"); r(12, 50, 30, 52, "chair"); r(20, 53, 21, 64, "chair"); r(14, 65, 28, 66, "chair")
    r(1, 59, 7, 66, "pot"); r(3, 53, 4, 58, "plant"); r(5, 51, 6, 58, "plant"); r(1, 55, 2, 57, "plant"); r(7, 54, 8, 56, "plant")

    # The person, facing right: legs under the desk, torso, head with hair, an eye that blinks.
    r(22, 48, 40, 51, "pants"); r(38, 52, 40, 64, "pants"); r(38, 65, 44, 66, "ink")
    r(17, 33, 28, 49, "shirt")
    r(22, 30, 24, 32, "skin")
    r(18, 19, 29, 30, "skin")
    r(17, 17, 29, 21, "hair"); r(17, 17, 19, 26, "hair")
    if t % 12 == 7:
        r(26, 24, 27, 24, "eye")
    else:
        r(26, 23, 27, 24, "eye")
    r(28, 27, 29, 27, "eye")

    # Desk top, keyboard and the arm reaching it; the two hands tap in turn.
    r(30, 46, 94, 47, "desk"); r(91, 48, 92, 66, "desk")
    r(36, 44, 50, 45, "key"); d.line([37, 44, 49, 44], fill=p["ink"])
    r(23, 35, 27, 42, "shirt"); r(27, 40, 37, 43, "shirt")
    up = (t // 2) % 2
    r(38, 42 - up, 40, 43 - up, "skin"); r(43, 42 - (1 - up), 45, 43 - (1 - up), "skin")

    # Monitor with scrolling code and a blinking cursor.
    r(50, 12, 82, 38, "frame"); r(52, 14, 80, 36, "screen"); r(64, 39, 67, 43, "frame"); r(59, 44, 72, 45, "frame")
    shift = (t // 3) % len(CODE)
    for row in range(7):
        ind, length, col = CODE[(row + shift) % len(CODE)]
        y = 16 + row * 3
        r(54 + ind, y, min(54 + ind + length, 77), y, col)
    if (t // 3) % 2 == 0:
        ind, length, _ = CODE[(6 + shift) % len(CODE)]
        x = min(54 + ind + length + 2, 78)
        r(x, 33, x, 35, "ink")

    # Coffee with rising steam.
    r(85, 40, 89, 45, "mug"); r(90, 41, 91, 43, "mug")
    for k in range(3):
        y = 38 - ((t + k * 3) % 8)
        x = 86 + (k % 2) + ((t + k) // 2) % 2
        d.point([x, y], fill=p["steam"])

    return im.crop((0, TOP, W, TOP + H)).resize((W * SCALE, H * SCALE), Image.NEAREST)


def save(theme: str) -> None:
    p = PALETTES[theme]
    colours = sorted(set(p.values()))
    flat = [0, 0, 0] + [v for c in colours for v in c]          # palette index 0 is the transparent colour
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat + [0] * (768 - len(flat)))
    out = []
    for t in range(FRAMES):
        im = frame(p, t)
        q = im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)
        q.paste(0, mask=im.getchannel("A").point(lambda a: 0 if a else 255))
        out.append(q)
    path = HERE / f"dev-{theme}.gif"
    out[0].save(path, save_all=True, append_images=out[1:], duration=MS, loop=0, transparency=0, disposal=2, optimize=False)
    print(f"wrote {path.relative_to(HERE.parent)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    save("light")
    save("dark")
