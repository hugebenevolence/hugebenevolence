"""Builds the animated SVG assets of the profile README (header, typing line, project cards, footer).
Self-hosted SVG with SMIL animation: no third-party image service, renders in GitHub's <img> in every theme.
    python3 assets/build.py"""
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', 'JetBrains Mono', Consolas, 'DejaVu Sans Mono', monospace"
G0, G1, G2, G3, G4 = "#0B1F17", "#1B4332", "#2D6A4F", "#52B788", "#B7E4C7"


def write(name: str, svg: str) -> None:
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg.strip() + "\n", encoding="utf-8")
    print("wrote", path.relative_to(HERE.parent))


def fade(delay: float, dur: float = 1.2) -> str:
    """Fade in once after `delay` seconds (keyTimes keep the start invisible without a flash)."""
    k = delay / (delay + dur)
    return f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{k:.3f};1" dur="{delay + dur}s" fill="freeze"/>'


# ---- header ------------------------------------------------------------------------------------------------------------------------
def header() -> None:
    w, h = 1200, 300
    wave_a = "M0,0 H1200 V238 C980,292 760,212 560,248 C360,284 180,230 0,262 Z"
    wave_b = "M0,0 H1200 V252 C1000,214 780,286 560,240 C340,206 170,282 0,248 Z"
    layers = [(905, [95, 150, 205]), (1005, [68, 122, 176, 230]), (1105, [95, 150, 205])]
    nodes = [(x, y) for x, ys in layers for y in ys]
    links = []
    for (xa, ya_list), (xb, yb_list) in zip(layers, layers[1:]):
        for ya in ya_list:
            for yb in yb_list:
                links.append((xa, ya, xb, yb))
    link_svg = "\n".join(
        f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{G4}" stroke-opacity="0.22" stroke-width="1.2" stroke-dasharray="4 7">'
        f'<animate attributeName="stroke-dashoffset" values="0;-22" dur="{2.2 + (k % 5) * 0.35:.2f}s" repeatCount="indefinite"/></line>'
        for k, (a, b, c, d) in enumerate(links))
    node_svg = "\n".join(
        f'<circle cx="{x}" cy="{y}" r="7" fill="{G3}" fill-opacity="0.55" stroke="{G4}" stroke-opacity="0.7" stroke-width="1.5">'
        f'<animate attributeName="fill-opacity" values="0.25;0.85;0.25" dur="3s" begin="{(k * 0.37) % 3:.2f}s" repeatCount="indefinite"/></circle>'
        for k, (x, y) in enumerate(nodes))
    write("header.svg", f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Trần Đại Nhân, Applied AI Engineer">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1" spreadMethod="reflect">
      <stop offset="0" stop-color="{G0}"/><stop offset="0.55" stop-color="{G1}"/><stop offset="1" stop-color="{G2}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-0.15 0;0.15 0;-0.15 0" dur="14s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <path d="{wave_a}" fill="url(#bg)">
    <animate attributeName="d" values="{wave_a};{wave_b};{wave_a}" dur="9s" repeatCount="indefinite"/>
  </path>
  <g>{link_svg}
{node_svg}</g>
  <g font-family="{SANS}">
    <text x="80" y="112" font-size="56" font-weight="700" fill="#FFFFFF">Trần Đại Nhân{fade(0.0)}</text>
    <text x="82" y="156" font-size="23" font-weight="600" fill="#D8F3DC">Applied AI Engineer{fade(0.5)}</text>
    <text x="82" y="190" font-size="18" fill="{G4}">AI Researcher &amp; Teaching Assistant at AI VIET NAM{fade(0.9)}</text>
    <text x="82" y="222" font-size="13.5" font-weight="600" letter-spacing="2" fill="#95D5B2">LLM AGENTS  ·  SPEECH &amp; NLP  ·  TEXT-TO-SQL  ·  RAG  ·  MULTIMODAL{fade(1.3)}</text>
  </g>
</svg>''')


# ---- typing line -------------------------------------------------------------------------------------------------------------------
def typing() -> None:
    lines = ["Building LLM agents that act safely on real tools",
             "Vietnamese speech, NLP, text-to-SQL and RAG",
             "Zalo AI Challenge 2026: Track 1 and Track 2 solutions",
             "Open to full-time roles in AI and backend engineering"]
    w, h, size, char = 900, 56, 21, 21 * 0.602
    n, slot = len(lines), 5.0
    cycle = n * slot
    parts = []
    for i, text in enumerate(lines):
        tw = len(text) * char
        left = (w - tw) / 2
        s, e = i / n, (i + 1) / n
        a, b, c = s + 0.42 / n, s + 0.86 / n, s + 0.96 / n
        keys = [0.0, s, a, b, c, e, 1.0]
        widths = [0, 0, tw, tw, 0, 0, 0]
        pts = [(k, v) for k, v in zip(keys, widths)]
        dedup = []
        for k, v in pts:                       # keyTimes must increase strictly
            if dedup and abs(dedup[-1][0] - k) < 1e-9:
                dedup[-1] = (k, v)
            else:
                dedup.append((k, v))
        kt = ";".join(f"{k:.4f}" for k, _ in dedup)
        wv = ";".join(f"{v:.1f}" for _, v in dedup)
        xv = ";".join(f"{left + v:.1f}" for _, v in dedup)
        vis_keys = sorted({0.0, s, e} - {1.0})
        vis_vals = ["1" if s <= k < e else "0" for k in vis_keys]
        vk = ";".join(f"{k:.4f}" for k in vis_keys)
        vv = ";".join(vis_vals)
        base_w = tw if i == 0 else 0
        parts.append(f'''
  <clipPath id="c{i}"><rect x="{left:.1f}" y="0" height="{h}" width="{base_w:.1f}">
    <animate attributeName="width" values="{wv}" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/></rect></clipPath>
  <text x="{left:.1f}" y="36" clip-path="url(#c{i})">{escape(text)}</text>
  <rect x="{left + base_w + 2:.1f}" y="15" width="3" height="27" fill="{G2}" opacity="{1 if i == 0 else 0}">
    <animate attributeName="x" values="{xv}" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="{vv}" keyTimes="{vk}" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite"/></rect>''')
    write("typing.svg", f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(' / '.join(lines))}">
  <g font-family="{MONO}" font-size="{size}" font-weight="500" fill="{G2}">{"".join(parts)}
  </g>
</svg>''')


# ---- project cards ----------------------------------------------------------------------------------------------------------------
THEMES = {"light": {"bg": "#FFFFFF", "border": "#D0D7DE", "title": "#0969DA", "text": "#57606A", "pill": "#DAFBE1", "pill_text": "#1A7F37"},
          "dark": {"bg": "#0D1117", "border": "#30363D", "title": "#58A6FF", "text": "#8B949E", "pill": "#12261E", "pill_text": "#3FB950"}}
LANG = {"Python": "#3572A5", "Jupyter Notebook": "#DA5B0B"}
BOOK = "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
CARDS = [
    ("lifemate", "ZaloAI-Challenge-lifemate", ["Spoken Vietnamese requests to verified tool calls:", "Gipformer ASR and a Qwen3.5-4B LoRA agent."],
     "Python", "Track 1 · public 61.26"),
    ("datamate", "zalo-ai-challenge-datamate-26", ["Text-to-SQL over heterogeneous Vietnamese retail", "data: Qwen3.5-9B LoRA, DuckDB, voting."],
     "Python", "Track 2 · public PA 0.683"),
    ("vivqa", "ViVQA-GPT-OSS-DRA", ["Difficulty-aware adaptive reasoning for", "Vietnamese visual question answering with GPT-OSS."],
     "Python", "AICI 2026 · ★ 4"),
    ("rag", "RAG-Enhancement", ["Full-stack platform benchmarking Vietnamese", "retrieval: FastAPI, Next.js, Redis workers."],
     "Jupyter Notebook", "RAG research"),
]


def cards() -> None:
    w, h = 420, 132
    for key, title, desc, lang, pill in CARDS:
        for theme, c in THEMES.items():
            pill_w = 18 + len(pill) * 6.6
            write(f"cards/{key}-{theme}.svg", f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(title)}: {escape(' '.join(desc))}">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{c['bg']}" stroke="{c['border']}"/>
  <g transform="translate(20 20)"><path d="{BOOK}" fill="{c['text']}"/></g>
  <g font-family="{SANS}">
    <text x="44" y="33" font-size="16" font-weight="600" fill="{c['title']}">{escape(title)}</text>
    <text x="20" y="62" font-size="13.5" fill="{c['text']}">{escape(desc[0])}</text>
    <text x="20" y="82" font-size="13.5" fill="{c['text']}">{escape(desc[1])}</text>
    <circle cx="26" cy="110" r="6" fill="{LANG[lang]}"/>
    <text x="38" y="114.5" font-size="12.5" fill="{c['text']}">{escape(lang)}</text>
    <rect x="{w - 20 - pill_w:.1f}" y="97" width="{pill_w:.1f}" height="24" rx="12" fill="{c['pill']}"/>
    <text x="{w - 20 - pill_w / 2:.1f}" y="113.5" font-size="12" font-weight="600" text-anchor="middle" fill="{c['pill_text']}">{escape(pill)}</text>
  </g>
</svg>''')


# ---- footer -----------------------------------------------------------------------------------------------------------------------
def footer() -> None:
    a = "M0,120 V58 C220,18 420,92 640,52 C860,12 1020,80 1200,44 V120 Z"
    b = "M0,120 V46 C240,84 440,14 660,58 C880,98 1040,26 1200,60 V120 Z"
    write("footer.svg", f'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" width="1200" height="120" role="img" aria-label="footer">
  <defs><linearGradient id="fg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{G2}"/><stop offset="0.5" stop-color="{G1}"/><stop offset="1" stop-color="{G0}"/></linearGradient></defs>
  <path d="{a}" fill="url(#fg)"><animate attributeName="d" values="{a};{b};{a}" dur="9s" repeatCount="indefinite"/></path>
</svg>''')


if __name__ == "__main__":
    header(); typing(); cards(); footer()
