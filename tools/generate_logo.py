"""Builds the proposed Blue Route Logistics logo files (text converted to outlines,
so the SVGs render identically everywhere without the font installed).

Run:  python3 tools/generate_logo.py
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONT_DIR = Path("/usr/share/fonts/opentype/inter")
OUT = Path(__file__).resolve().parent.parent / "static" / "img"
OUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, CYAN, WHITE = "#0B1F3A", "#2563EB", "#38BDF8", "#FFFFFF"


def text_path(text, font_file, size, x, y, tracking=0.0):
    font = TTFont(FONT_DIR / font_file)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    pen = SVGPathPen(gs)
    cursor = 0.0
    for ch in text:
        gname = cmap[ord(ch)]
        tp = TransformPen(pen, (scale, 0, 0, -scale, x + cursor, y))
        gs[gname].draw(tp)
        cursor += gs[gname].width * scale + tracking * size
    return pen.getCommands(), cursor - tracking * size


def mark(fg_tile, route, start, end, ox=0, oy=0, s=1.0):
    """48x48 mark: a rounded tile with a two-stop route that climbs up and to the right."""
    t = f'transform="translate({ox} {oy}) scale({s})"'
    return f'''<g {t}>
    <rect width="48" height="48" rx="12" fill="{fg_tile}"/>
    <path d="M14 33.5V27a6 6 0 0 1 6-6h8a6 6 0 0 0 6-6v-2" fill="none" stroke="{route}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="14" cy="34" r="4.2" fill="{fg_tile}" stroke="{start}" stroke-width="3"/>
    <circle cx="34" cy="13" r="4.6" fill="{end}"/>
  </g>'''


def lockup(name_color, sub_color, tile, route, start, end, bg=None):
    name_d, name_w = text_path("Blue Route", "InterDisplay-Bold.otf", 25, 62, 25, tracking=-0.015)
    sub_d, sub_w = text_path("LOGISTICS", "Inter-SemiBold.otf", 10.5, 63, 42, tracking=0.28)
    width = round(62 + max(name_w, sub_w) + 4)
    bg_rect = f'<rect width="{width}" height="48" fill="{bg}"/>' if bg else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 48" width="{width * 4}" height="192" role="img" aria-label="Blue Route Logistics">
  <!-- Blue Route Logistics: proposed logo concept, pending approval -->
  {bg_rect}
  {mark(tile, route, start, end)}
  <path d="{name_d}" fill="{name_color}"/>
  <path d="{sub_d}" fill="{sub_color}"/>
</svg>
'''


(OUT / "logo.svg").write_text(lockup(NAVY, BLUE, NAVY, WHITE, CYAN, CYAN))
(OUT / "logo-white.svg").write_text(lockup(WHITE, CYAN, WHITE, NAVY, BLUE, BLUE))
(OUT / "logo-mark.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="192" height="192" role="img" aria-label="Blue Route Logistics">\n'
    "  <!-- Blue Route Logistics: proposed logo mark, pending approval -->\n  "
    + mark(NAVY, WHITE, CYAN, CYAN) + "\n</svg>\n")
(OUT / "favicon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">' + mark(NAVY, WHITE, CYAN, CYAN) + "</svg>\n")
print("logo files written to", OUT)
