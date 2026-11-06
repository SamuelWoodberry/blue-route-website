"""Renders PNG assets (favicons, social share image) from the SVG logo using headless Chrome.
Run: python3 tools/render_images.py   (requires Playwright + Chrome; output committed in static/img)"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "static" / "img"
FONTS = (ROOT / "static" / "fonts").as_uri()
mark = (IMG / "favicon.svg").read_text()
lines = (IMG / "route-lines.svg").as_uri()
logo = (IMG / "logo-white.svg").as_uri()
og = f"""<html><head><style>
@font-face{{font-family:D;src:url({FONTS}/InterDisplay-Bold.woff)}}
@font-face{{font-family:I;src:url({FONTS}/Inter-Medium.woff)}}
body{{margin:0;width:1200px;height:630px;background:#0B1F3A;position:relative;overflow:hidden;font-family:I}}
.l{{position:absolute;right:-60px;top:40px;width:640px;height:640px;background:url({lines}) center/contain no-repeat;opacity:.9}}
.c{{position:absolute;left:80px;top:72px;width:760px}}
img{{height:64px}} h1{{font-family:D;color:#fff;font-size:68px;line-height:1.04;letter-spacing:-2px;margin:70px 0 28px}}
p{{color:#C9D6E8;font-size:28px;margin:0;line-height:1.4}}
</style></head><body><div class=l></div><div class=c><img src="{logo}">
<h1>Pharmacy &amp; medical courier services</h1><p>Port St. Lucie · Fort Pierce · Stuart · Jensen Beach, FL</p></div></body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    def shot(html, w, h, out):
        pg = b.new_page(viewport={"width": w, "height": h})
        tmp = IMG.parent / "_render.html"; tmp.write_text(html)
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(800); tmp.unlink()
        pg.screenshot(path=str(IMG / out)); pg.close()
    shot(og, 1200, 630, "og-image.png")
    for size, name, pad in [(32, "favicon-32.png", 0), (180, "apple-touch-icon.png", 18), (512, "logo-mark.png", 0)]:
        bg = "#0B1F3A" if pad else "transparent"
        html = f"<html><body style='margin:0;background:{bg}'><div style='padding:{pad}px;width:{size-2*pad}px;height:{size-2*pad}px'>{mark.replace('<svg ', '<svg width=100% height=100% ')}</div></body></html>"
        pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(html); pg.wait_for_timeout(200)
        pg.screenshot(path=str(IMG / name), omit_background=not pad); pg.close()
    b.close()
print("rendered")
