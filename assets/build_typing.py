"""Typing line under the name in the profile README: assets/typing-light.svg and assets/typing-dark.svg.

Each line is typed, held, deleted, then the next one starts. The animation is plain SMIL (a clip rectangle whose width steps
one character at a time, and a caret that follows it), so it plays inside an <img> without scripts. Character width is
taken as 0.6 em, which matches the common monospace fonts closely enough to centre each line. Run:

    python3 assets/build_typing.py
"""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINES = ["Reading research papers", "Reproducing them in code", "Teaching NLP and multimodal AI", "Building LLM systems"]
W, H, FS = 560, 36, 20
CW = 0.6 * FS
TYPE, HOLD, DELETE, PAUSE = 0.065, 1.5, 0.03, 0.35
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
THEMES = {"light": {"fg": "#1f2328", "caret": "#0969da"}, "dark": {"fg": "#e6edf3", "caret": "#4493f8"}}


def slots() -> tuple[list[tuple[float, float, float]], float]:
    """(start, end of typing, end of the slot) for each line, and the loop length."""
    out, t = [], 0.0
    for line in LINES:
        typed = t + len(line) * TYPE
        end = typed + HOLD + len(line) * DELETE + PAUSE
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


def build(c: dict) -> str:
    spans, total = slots()
    parts = []
    for i, (line, (start, typed, end)) in enumerate(zip(LINES, spans)):
        n, x0 = len(line), round((W - len(line) * CW) / 2, 1)
        delete_from = typed + HOLD
        events = [(0.0, 0)] + [(start + k * TYPE, k * CW) for k in range(1, n + 1)]
        events += [(delete_from + (n - k) * DELETE, k * CW) for k in range(n - 1, -1, -1)]
        kt, vals = track(events, total)
        caret_x = ";".join(f"{x0 + float(v) + 2:g}" for v in vals.split(";"))
        show_kt, show_vals = track([(0.0, 0), (start, 1), (end - PAUSE, 0)], total)
        anim = f'dur="{total:.3f}s" repeatCount="indefinite" calcMode="discrete"'
        parts.append(f'''  <clipPath id="clip{i}"><rect x="{x0}" y="0" width="0" height="{H}"><animate attributeName="width" {anim} keyTimes="{kt}" values="{vals}"/></rect></clipPath>
  <text x="{x0}" y="25" clip-path="url(#clip{i})" font-family="{MONO}" font-size="{FS}" fill="{c["fg"]}">{escape(line)}</text>
  <rect x="{x0 + 2}" y="8" width="2.5" height="22" fill="{c["caret"]}" opacity="0">
    <animate attributeName="x" {anim} keyTimes="{kt}" values="{caret_x}"/>
    <animate attributeName="opacity" {anim} keyTimes="{show_kt}" values="{show_vals}"/>
  </rect>''')
    label = escape(". ".join(LINES) + ".", quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
{chr(10).join(parts)}
</svg>
'''


def main() -> None:
    for theme, c in THEMES.items():
        (HERE / f"typing-{theme}.svg").write_text(build(c), encoding="utf-8")
    print(f"wrote assets/typing-light.svg and assets/typing-dark.svg (loop {slots()[1]:.1f} s)")


if __name__ == "__main__":
    main()
