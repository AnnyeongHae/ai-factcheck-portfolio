"""
카드뉴스 자동 생성기 (Card News Generator)
-------------------------------------------
팩트체크 도시에(dossier) 데이터를 인스타그램/X 최적화 카드뉴스 이미지로 변환합니다.

Usage:
    python tools/generate_card_news.py --latest 3 --format both
    python tools/generate_card_news.py --case 2026-09-03_sns_geeknews_m4_pro_mac_mini_local_llm
    python tools/generate_card_news.py --all --format instagram
"""
import argparse
import json
from pathlib import Path
import textwrap
from datetime import datetime
import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow (PIL) is not installed.")
    print("Please install it using: pip install Pillow")
    sys.exit(1)

# ─── Verdict → Color / Label mappings ────────────────────────────
VERDICT_COLORS = {
    'VERIFIED_TRUE': '#22C55E',
    'HALF_TRUE':     '#F59E0B',
    'GAMED':         '#EF4444',
    'GAMED_CLAIM':   '#EF4444',
    'EXAGGERATED':   '#EF4444',
    'MISLEADING':    '#EF4444',
    'FALSE':         '#DC2626',
}

VERDICT_LABELS_KO = {
    'VERIFIED_TRUE': 'VERIFIED TRUE',
    'HALF_TRUE':     'HALF TRUE',
    'GAMED':         'GAMED',
    'GAMED_CLAIM':   'GAMED',
    'EXAGGERATED':   'EXAGGERATED',
    'MISLEADING':    'MISLEADING',
    'FALSE':         'FALSE',
}

VERDICT_EMOJI = {
    'VERIFIED_TRUE': 'V',
    'HALF_TRUE':     '!',
    'GAMED':         'X',
    'GAMED_CLAIM':   'X',
    'EXAGGERATED':   'X',
    'MISLEADING':    'X',
    'FALSE':         'X',
}

# ─── Windows Font discovery ──────────────────────────────────────
FONT_PATHS_REGULAR = [
    r'C:\Windows\Fonts\malgun.ttf',      # 맑은 고딕
    r'C:\Windows\Fonts\segoeui.ttf',
]
FONT_PATHS_BOLD = [
    r'C:\Windows\Fonts\malgungbd.ttf',   # 맑은 고딕 Bold
    r'C:\Windows\Fonts\segoeuib.ttf',
]


def _find_font(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_font(size, bold=False):
    return _find_font(FONT_PATHS_BOLD if bold else FONT_PATHS_REGULAR, size)


# ─── Text utilities ──────────────────────────────────────────────
def wrap_korean(text: str, max_chars: int, max_lines: int = 99) -> str:
    """Word-wrap that respects Korean text and truncates with '…' if too long."""
    if not text:
        return ""
    lines = []
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=max_chars)
        lines.extend(wrapped)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max_chars - 1] + '…'
    return '\n'.join(lines)


def _text_height(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    """Measure multi-line text height via textbbox."""
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


# ─── Card renderer ───────────────────────────────────────────────
def generate_card(dossier_data: dict, output_path: Path, format_type: str = 'instagram'):
    """Render a single card news image."""

    # ── Layout presets per format ──
    if format_type == 'instagram':
        W, H = 1080, 1080
        PAD = 60
        BAR = 24
        HEADER_SIZE    = 40
        HOOK_SIZE      = 52
        VERDICT_SIZE   = 40
        BODY_SIZE      = 34
        FOOTER_SIZE    = 28
        HOOK_WRAP      = 18
        HOOK_MAX_LINES = 5
        BODY_WRAP      = 28
    else:  # twitter
        W, H = 1200, 675
        PAD = 48
        BAR = 18
        HEADER_SIZE    = 32
        HOOK_SIZE      = 40
        VERDICT_SIZE   = 32
        BODY_SIZE      = 28
        FOOTER_SIZE    = 22
        HOOK_WRAP      = 24
        HOOK_MAX_LINES = 3
        BODY_WRAP      = 36

    # ── Fonts ──
    f_header  = get_font(HEADER_SIZE, bold=True)
    f_hook    = get_font(HOOK_SIZE)
    f_verdict = get_font(VERDICT_SIZE, bold=True)
    f_body    = get_font(BODY_SIZE)
    f_footer  = get_font(FOOTER_SIZE)

    # ── Data extraction ──
    verdict     = dossier_data.get('verdict', 'GAMED')
    color       = VERDICT_COLORS.get(verdict, '#EF4444')
    label       = VERDICT_LABELS_KO.get(verdict, verdict)
    portfolio   = dossier_data.get('portfolio_story', {})
    hook_raw    = portfolio.get('the_hook', dossier_data.get('title_ko', ''))
    takeaways_raw = portfolio.get('engineering_takeaways', '')
    if isinstance(takeaways_raw, str):
        # Split numbered items like "1. xxx\n2. yyy"
        takeaways = [t.strip() for t in takeaways_raw.split('\n') if t.strip()]
    else:
        takeaways = list(takeaways_raw) if takeaways_raw else []

    # ── Canvas ──
    img  = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Color bars
    draw.rectangle([0, 0, W, BAR], fill=color)
    draw.rectangle([0, H - BAR, W, H], fill=color)

    # Footer zone (reserve space from bottom)
    footer_zone = FOOTER_SIZE * 2 + 30 + PAD + BAR
    content_max_y = H - footer_zone  # content must not exceed this

    y = BAR + PAD

    # ── Header ──
    header_text = "AI FACT-CHECK"
    draw.text((PAD, y), header_text, font=f_header, fill='#6B7280')
    y += HEADER_SIZE + 8
    draw.line([(PAD, y), (PAD + 280, y)], fill=color, width=3)
    y += 30

    # ── Hook claim ──
    hook_text = wrap_korean(hook_raw, HOOK_WRAP, HOOK_MAX_LINES)
    hook_h = _text_height(draw, hook_text, f_hook)
    draw.multiline_text((PAD, y), hook_text, font=f_hook, fill='#111827',
                        spacing=8)
    y += hook_h + 36

    # ── Verdict badge (filled rectangle) ──
    badge_text = f" {label} "
    bbox = f_verdict.getbbox(badge_text)
    bw = bbox[2] - bbox[0] + 32
    bh = bbox[3] - bbox[1] + 20
    # Background pill
    draw.rounded_rectangle([PAD, y, PAD + bw, y + bh], radius=8, fill=color)
    draw.text((PAD + 16, y + 8), badge_text, font=f_verdict, fill='#FFFFFF')
    y += bh + 32

    # ── Takeaways (only if room) ──
    if y < content_max_y - BODY_SIZE * 3 and takeaways:
        draw.text((PAD, y), "MEASURED RESULTS:", font=get_font(BODY_SIZE - 4, bold=True),
                  fill='#6B7280')
        y += BODY_SIZE + 8

        for ta in takeaways[:2]:
            if y >= content_max_y - BODY_SIZE * 2:
                break
            # Clean numbering prefixes like "1. "
            ta_clean = ta.lstrip('0123456789. ')
            if len(ta_clean) > BODY_WRAP * 2:
                ta_clean = ta_clean[:BODY_WRAP * 2 - 1] + '…'
            ta_wrapped = wrap_korean(ta_clean, BODY_WRAP, max_lines=2)
            ta_h = _text_height(draw, ta_wrapped, f_body)
            draw.multiline_text((PAD + 10, y), f"▸ {ta_wrapped}", font=f_body,
                                fill='#374151', spacing=4)
            y += ta_h + 14

    # ── Footer ──
    fy = H - BAR - PAD - FOOTER_SIZE * 2 - 10
    draw.line([(PAD, fy - 12), (W - PAD, fy - 12)], fill='#E5E7EB', width=2)
    draw.text((PAD, fy), "@ai_factcheck_kr", font=f_footer, fill='#9CA3AF')
    draw.text((PAD, fy + FOOTER_SIZE + 6),
              "annyeonghae.github.io/ai-factcheck-portfolio",
              font=f_footer, fill='#9CA3AF')

    img.save(output_path, quality=95)
    return output_path


# ─── CLI ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate social-media card news from factcheck dossiers.")
    parser.add_argument('--latest', type=int, default=3,
                        help="Generate for N most recent dossiers (default: 3)")
    parser.add_argument('--case', type=str,
                        help="Generate for a specific case ID")
    parser.add_argument('--all', action='store_true',
                        help="Generate for all dossiers")
    parser.add_argument('--format',
                        choices=['instagram', 'twitter', 'both'],
                        default='both', help="Output format (default: both)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    investigations_dir = project_root / 'investigations'
    public_dir = project_root / 'public' / 'card-news'
    public_dir.mkdir(parents=True, exist_ok=True)

    # ── Collect dossiers ──
    dossiers = []
    if args.case:
        meta = investigations_dir / args.case / 'metadata.json'
        if meta.exists():
            with open(meta, 'r', encoding='utf-8') as f:
                d = json.load(f); d['_case_id'] = args.case
                dossiers.append(d)
        else:
            print(f"Case not found: {args.case}"); return
    else:
        for cdir in investigations_dir.iterdir():
            if not cdir.is_dir():
                continue
            meta = cdir / 'metadata.json'
            if meta.exists():
                try:
                    with open(meta, 'r', encoding='utf-8') as f:
                        d = json.load(f); d['_case_id'] = cdir.name
                        dossiers.append(d)
                except Exception as e:
                    print(f"⚠ Skipped {cdir.name}: {e}")

    dossiers.sort(key=lambda x: x.get('investigation_date', ''), reverse=True)
    if not args.all and not args.case:
        dossiers = dossiers[:args.latest]

    # ── Generate ──
    generated = 0
    for dossier in dossiers:
        date_str = dossier.get('investigation_date', 'unknown')
        cid = dossier['_case_id']
        base = f"{date_str}_{cid}"

        for fmt in (['instagram', 'twitter'] if args.format == 'both'
                     else [args.format]):
            suffix = 'ig' if fmt == 'instagram' else 'tw'
            out = public_dir / f"{base}_{suffix}.png"
            try:
                generate_card(dossier, out, fmt)
                generated += 1
                print(f"  [{suffix.upper()}] {out.name}")
            except Exception as e:
                print(f"  FAIL [{suffix.upper()}] {cid}: {e}")

    print(f"\n[OK] Generated {generated} card(s) -> {public_dir}")


if __name__ == '__main__':
    main()
