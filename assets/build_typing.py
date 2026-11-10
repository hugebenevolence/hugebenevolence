"""Terminal-style typing line under the name in the profile README: assets/typing.svg.

A small dark terminal window (the night palette of the room GIF, so it sits well on light and dark GitHub themes) types one
line after a coloured prompt, holds it, backspaces it, and types the next. Key words are highlighted. The animation is plain
SMIL (a clip rectangle whose width steps one character at a time, and a block cursor that follows it), so it plays inside an
<img> without scripts. Each text run is pinned to 0.6 em per character with textLength, so the cursor stays on the last
letter whatever monospace font the viewer has. Run:

    python3 assets/build_typing.py
"""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
# each line is a list of (text, highlighted?)
LINES = [
    [("Building ", False), ("reliable, production-grade AI", True)],
    [("Translating ", False), ("research", True), (" into ", False), ("real-world impact", True)],
    [("Evaluating models with ", False), ("scientific rigor", True)],
    [("Mentoring the ", False), ("next generation", True), (" of AI talent", False)],
]
W, H, FS = 680, 84, 18
CW = 0.6 * FS
X0, BASE = 22, 62                                    # left margin and text baseline
TYPE, HOLD, DELETE, PAUSE = 0.06, 1.8, 0.025, 0.4
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
C = {"bg": "#161b2e", "bar": "#1d2340", "edge": "#2c3358", "muted": "#6a72a8", "text": "#e4e6f2", "hi": "#f0c864",
     "user": "#78c882", "path": "#88a6ff", "dot_r": "#ec6e6e", "dot_y": "#f0c864", "dot_g": "#78c882"}
PROMPT = [("nhan@lab", "user"), (":", "muted"), ("~", "path"), ("$ ", "muted")]


def slots() -> tuple[list[tuple[float, float, float]], float]:
    out, t = [], 0.0
    for line in LINES:
        n = sum(len(s) for s, _ in line)
        typed = t + n * TYPE
        end = typed + HOLD + n * DELETE + PAUSE
        out.append((t, typed, end))
        t = end
    return out, t


def track(events: list[tuple[float, float]], total: float) -> tuple[str, str]:
    """keyTimes and values for a discrete animation from (time, value) events."""
    times, values = [], []
    for time, value in events:
        if values and value == values[-1]:
            continue
        if times and time <= times[-1] * total + 1e-6:
            times.pop(); values.pop()
        times.append(time / total); values.append(value)
    return ";".join(f"{k:.5f}" for k in times), ";".join(f"{v:g}" for v in values)


def runs(parts: list[tuple[str, str]], x: float) -> str:
    """Text runs placed one after another, each pinned to its character count."""
    out = []
    for text, colour in parts:
        out.append(f'<text x="{x:g}" y="{BASE}" textLength="{len(text) * CW:g}" lengthAdjust="spacing" xml:space="preserve" '
                   f'font-family="{MONO}" font-size="{FS}" fill="{C[colour]}">{escape(text)}</text>')
        x += len(text) * CW
    return "".join(out)


def build() -> str:
    spans, total = slots()
    prompt_w = sum(len(s) for s, _ in PROMPT) * CW
    tx = X0 + prompt_w
    body, cursors = [], []
    for i, (line, (start, typed, end)) in enumerate(zip(LINES, spans)):
        n = sum(len(s) for s, _ in line)
        delete_from = typed + HOLD
        events = [(0.0, 0)] + [(start + k * TYPE, k * CW) for k in range(1, n + 1)]
        events += [(delete_from + (n - k) * DELETE, k * CW) for k in range(n - 1, -1, -1)]
        kt, vals = track(events, total)
        cursor_x = ";".join(f"{tx + float(v):g}" for v in vals.split(";"))
        show_kt, show_vals = track([(0.0, 0), (start, 1), (end - PAUSE, 0)], total)
        anim = f'dur="{total:.3f}s" repeatCount="indefinite" calcMode="discrete"'
        parts = [(text, "hi" if hi else "text") for text, hi in line]
        body.append(f'''  <clipPath id="clip{i}"><rect x="{tx:g}" y="30" width="0" height="{H - 30}"><animate attributeName="width" {anim} keyTimes="{kt}" values="{vals}"/></rect></clipPath>
  <g clip-path="url(#clip{i})">{runs(parts, tx)}</g>''')
        cursors.append(f'''    <rect x="{tx:g}" y="{BASE - 15}" width="{CW:g}" height="20" fill="{C["text"]}" opacity="0">
      <animate attributeName="x" {anim} keyTimes="{kt}" values="{cursor_x}"/>
      <animate attributeName="opacity" {anim} keyTimes="{show_kt}" values="{show_vals}"/>
    </rect>''')
    label = escape(". ".join("".join(t for t, _ in line) for line in LINES) + ".", quote=True)
    dots = "".join(f'<circle cx="{18 + 16 * k}" cy="15" r="5" fill="{C[d]}"/>' for k, d in enumerate(("dot_r", "dot_y", "dot_g")))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C["bg"]}" stroke="{C["edge"]}"/>
  <path d="M0.5 30 V10.5 a10 10 0 0 1 10 -10 H{W - 10.5} a10 10 0 0 1 10 10 V30 Z" fill="{C["bar"]}"/>
  <line x1="0.5" y1="30" x2="{W - 0.5}" y2="30" stroke="{C["edge"]}"/>
  {dots}
  <text x="{W / 2:g}" y="19.5" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{C["muted"]}">nhan@lab: ~</text>
  {runs(PROMPT, X0)}
{chr(10).join(body)}
  <g><animate attributeName="opacity" values="1;0.2" keyTimes="0;0.5" dur="1s" repeatCount="indefinite" calcMode="discrete"/>
{chr(10).join(cursors)}
  </g>
</svg>
'''


def main() -> None:
    (HERE / "typing.svg").write_text(build(), encoding="utf-8")
    print(f"wrote assets/typing.svg (loop {slots()[1]:.1f} s)")


if __name__ == "__main__":
    main()
