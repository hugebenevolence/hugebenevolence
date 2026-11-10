"""Borderless project and publication cards for the profile README: assets/cards/<key>-light.svg and <key>-dark.svg.

GitHub strips inline CSS from READMEs, so table cells always get borders; drawing each card as an SVG is the only way to get
a soft background without one. Text uses the system font stack, so every line is kept short enough to fit the card in the
widest common fallback font (checked here against DejaVu Sans when it is installed). Run:

    python3 assets/build_cards.py
"""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "cards"
W, H, PAD = 420, 148, 22
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
THEMES = {
    "light": {"bg": "#f1f4f8", "fg": "#1f2328", "muted": "#59636e", "accent": "#0969da"},
    "dark": {"bg": "#161b22", "fg": "#e6edf3", "muted": "#9198a1", "accent": "#4493f8"},
}

# key: (title, tag, [description line 1, line 2], result)
CARDS = {
    "bridge": ("BRIDGE", "Team lead · Vingroup AI Talent Program",
               ["Deployed research assistant for citation-grounded", "literature review and reproducibility audits."],
               "recall 46.7% vs 36.7% (Asta) · audit < $0.03"),
    "smile": ("S.M.I.L.E", "Capstone · booking, payments and identity",
              ["Dental practice platform on 4 NestJS services", "and 5 PostgreSQL databases, with VNPay and KYC."],
              "one booking per slot · no double charges"),
    "lifemate": ("LifeMate", "Zalo AI Challenge 2026 · Track 1",
                 ["Spoken Vietnamese requests to verified tool calls,", "with Gipformer ASR and a Qwen3.5-4B LoRA agent."],
                 "public score 61.26"),
    "datamate": ("DataMate", "Zalo AI Challenge 2026 · Track 2",
                 ["Questions over messy Vietnamese retail data,", "answered by a Qwen3.5-9B LoRA with voted SQL."],
                 "public PA 0.683"),
    "vlm": ("Vietnamese VLM", "Team project · pretrained from scratch",
            ["LLaVA-style SigLIP2 and Llama 3.2 1B: projector", "alignment, then Vietnamese instruction tuning."],
            "distributed, resumable training with Accelerate"),
    "gpt2": ("Vietnamese GPT-2", "Team project · pretrained from scratch",
             ["Own Vietnamese tokenizer and a GPT-2 trained on", "a deduplicated 2.64B-token news and wiki corpus."],
             "served with FastAPI and a Next.js chat"),
    "vqa": ("Difficulty-Aware Vietnamese VQA", "AICI 2026 · first author · Springer",
            ["Routes each question to low, medium or high", "reasoning effort from a CLIP caption score."],
            "inference 3,317 s → 815 s on ViVQA-X (−75%)"),
    "cot": ("Multi-Mode CoT Distillation", "ICISN 2026 · co-author",
            ["Curates GPT-OSS reasoning traces at three", "budgets to train a Llama 3.2 3B student."],
            "GSM8K 0.80 · MATH500 0.48 after GRPO"),
}


def card(title: str, tag: str, desc: list[str], result: str, c: dict) -> str:
    label = escape(f"{title}. {tag}. {' '.join(desc)} {result}", quote=True)
    lines = "\n".join(f'  <text x="{PAD}" y="{84 + 19 * i}" font-family="{SANS}" font-size="13.5" fill="{c["fg"]}">{escape(t)}</text>'
                      for i, t in enumerate(desc))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
  <rect width="{W}" height="{H}" rx="12" fill="{c["bg"]}"/>
  <text x="{PAD}" y="36" font-family="{SANS}" font-size="16.5" font-weight="600" fill="{c["fg"]}">{escape(title)}<tspan fill="{c["muted"]}" font-weight="400" dx="6">↗</tspan></text>
  <text x="{PAD}" y="57" font-family="{SANS}" font-size="12" fill="{c["muted"]}">{escape(tag)}</text>
{lines}
  <text x="{PAD}" y="128" font-family="{MONO}" font-size="11.5" fill="{c["accent"]}">{escape(result)}</text>
</svg>
'''


def check_widths() -> None:
    """Warn when a line would overflow in DejaVu Sans, which is wider than the fonts GitHub users usually have."""
    try:
        from PIL import ImageFont
        sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        fonts = {"title": ImageFont.truetype(sans.replace(".ttf", "-Bold.ttf"), 16.5), "tag": ImageFont.truetype(sans, 12),
                 "desc": ImageFont.truetype(sans, 13.5),
                 "result": ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11.5)}
    except (ImportError, OSError):
        return
    room = W - 2 * PAD
    for key, (title, tag, desc, result) in CARDS.items():
        for kind, text in [("title", title + "  ↗"), ("tag", tag), ("result", result)] + [("desc", t) for t in desc]:
            width = fonts[kind].getlength(text)
            if width > room:
                print(f"  overflow {key}.{kind}: {width:.0f} px > {room} px: {text}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for key, (title, tag, desc, result) in CARDS.items():
        for theme, c in THEMES.items():
            (OUT / f"{key}-{theme}.svg").write_text(card(title, tag, desc, result, c), encoding="utf-8")
    print(f"wrote {len(CARDS) * 2} cards to {OUT.relative_to(HERE.parent)}/")
    check_widths()


if __name__ == "__main__":
    main()
