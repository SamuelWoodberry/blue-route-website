#!/usr/bin/env python3
"""Blue Route Logistics static site builder.

No dependencies beyond Python 3.8+. Netlify runs this automatically on every deploy
(see netlify.toml). To build locally:  python3 build.py   -> output in dist/

  src/pages/*.html     page content (with a small JSON meta block at the top)
  src/partials/*       shared pieces: header, footer, map, CTA band, forms
  static/              CSS, JS, fonts, images (copied as-is)
  site.config.json     business details; empty values are hidden, never faked
"""
import datetime
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, STATIC, DIST = ROOT / "src", ROOT / "static", ROOT / "dist"
CFG = json.loads((ROOT / "site.config.json").read_text())

NAV = [
    ("index", "Home"),
    ("about", "About Us"),
    ("services", "Services"),
    ("service-areas", "Service Areas"),
    ("request-a-quote", "Request a Quote"),
    ("contact", "Contact Us"),
]
CITIES = [
    ("port-st-lucie", "Port St. Lucie"),
    ("fort-pierce", "Fort Pierce"),
    ("stuart", "Stuart"),
    ("jensen-beach", "Jensen Beach"),
]

missing = []


def cfg(key, label=None):
    val = CFG.get(key, "")
    if isinstance(val, str):
        val = val.strip()
    if not val and label:
        missing.append(label)
    return val


def e(s):
    return html.escape(str(s), quote=True)


def url_for(slug, root):
    return f"{root}" if slug == "index" else f"{root}{slug}/"


# ---------------------------------------------------------------- shared snippets
SITE_URL = cfg("site_url", "Website domain (site_url)").rstrip("/")
NAME = CFG["business_name"]
LEGAL = cfg("legal_name", "Legal LLC name (legal_name)") or NAME
PHONE = cfg("phone_display", "Business phone number (phone_display / phone_e164)")
PHONE_TEL = cfg("phone_e164") or re.sub(r"[^\d+]", "", PHONE)
EMAIL = cfg("email", "Business email (email)")
HOURS = CFG.get("hours") or []
if not HOURS:
    missing.append("Business hours (hours)")
SOCIAL = {k: v for k, v in (CFG.get("social") or {}).items() if v}
if not SOCIAL:
    missing.append("Social media / Google Business Profile links (social) - optional")
PLAUSIBLE = (CFG.get("analytics") or {}).get("plausible_domain", "")
POLICY_DATE = cfg("policy_effective_date", "Privacy Policy / Terms effective date (policy_effective_date)")
TESTIMONIALS = [t for t in CFG.get("testimonials", []) if t.get("approved")]
YEAR = datetime.date.today().year
LOCATION = f"{CFG['city']}, {CFG['state']}"

SOCIAL_LABELS = {"linkedin": "LinkedIn", "facebook": "Facebook",
                 "google_business_profile": "Google Business Profile", "instagram": "Instagram"}


def contact_list(css_class):
    items = []
    if PHONE:
        items.append(f'<li><span class="{css_class}__k">Phone</span><a href="tel:{e(PHONE_TEL)}">{e(PHONE)}</a></li>')
    if EMAIL:
        items.append(f'<li><span class="{css_class}__k">Email</span><a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a></li>')
    items.append(f'<li><span class="{css_class}__k">Based in</span><span>{e(LOCATION)}</span></li>')
    if HOURS:
        hrs = "<br>".join(f"{e(h['days'])}: {e(h['time'])}" for h in HOURS)
        items.append(f'<li><span class="{css_class}__k">Hours</span><span>{hrs}</span></li>')
    return f'<ul class="{css_class}">' + "".join(items) + "</ul>"


def social_list():
    if not SOCIAL:
        return ""
    links = "".join(
        f'<li><a href="{e(u)}" rel="noopener" target="_blank">{SOCIAL_LABELS.get(k, k.title())}'
        f'<span class="visually-hidden"> (opens in a new tab)</span></a></li>'
        for k, u in SOCIAL.items())
    return f'<ul class="footer__social" aria-label="Social media">{links}</ul>'


def contact_fallback():
    if PHONE and EMAIL:
        return f'call <a href="tel:{e(PHONE_TEL)}">{e(PHONE)}</a> or email <a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a>'
    if PHONE:
        return f'call <a href="tel:{e(PHONE_TEL)}">{e(PHONE)}</a>'
    if EMAIL:
        return f'email <a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a>'
    return "try again in a few minutes"


def testimonials_section():
    """Reusable testimonial component. Renders nothing until a real, approved testimonial exists."""
    if not TESTIMONIALS:
        return "<!-- Testimonials: hidden until approved customer feedback is added in site.config.json -->"
    cards = "".join(
        f'<figure class="quote"><blockquote><p>{e(t["quote"])}</p></blockquote>'
        f'<figcaption><strong>{e(t["name"])}</strong>'
        f'{"<span>" + e(t["role"]) + "</span>" if t.get("role") else ""}</figcaption></figure>'
        for t in TESTIMONIALS)
    return (f'<section class="section section--tint" aria-labelledby="t-h"><div class="container">'
            f'<h2 id="t-h" class="h2">What our clients say</h2><div class="quotes">{cards}</div></div></section>')


def schema(page_url):
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "@id": f"{SITE_URL}/#business",
        "name": NAME,
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/img/logo-mark.png",
        "image": f"{SITE_URL}/img/og-image.png",
        "description": "Locally operated pharmacy courier, medical supply delivery and dedicated route services for healthcare businesses on Florida's Treasure Coast.",
        "address": {"@type": "PostalAddress", "addressLocality": CFG["city"],
                    "addressRegion": CFG["state"], "addressCountry": "US"},
        "areaServed": [{"@type": "City", "name": f"{c}, FL"} for _, c in CITIES],
    }
    if PHONE_TEL:
        data["telephone"] = PHONE_TEL
    if EMAIL:
        data["email"] = EMAIL
    if HOURS:
        data["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["schema_days"],
             "opens": h["opens"], "closes": h["closes"]} for h in HOURS if h.get("schema_days")]
    if SOCIAL:
        data["sameAs"] = list(SOCIAL.values())
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


# ---------------------------------------------------------------- templating
def render(text, ctx, depth=0):
    if depth > 5:
        return text

    def include(m):
        return render((SRC / "partials" / m.group(1)).read_text(), ctx, depth + 1)

    text = re.sub(r"\{%\s*include\s+([\w.\-]+)\s*%\}", include, text)

    def var(m):
        key = m.group(1)
        if key not in ctx:
            sys.exit(f"Unknown template variable: {key}")
        return str(ctx[key])

    return re.sub(r"\{\{\s*([\w]+)\s*\}\}", var, text)


def parse_page(path):
    raw = path.read_text()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        sys.exit(f"{path.name}: missing <!--meta {{...}} --> block")
    return json.loads(m.group(1)), raw[m.end():]


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)

    pages = sorted((SRC / "pages").glob("*.html"))
    sitemap = []
    for path in pages:
        meta, body = parse_page(path)
        slug = path.stem
        depth = 0 if slug in ("index", "404") else 1
        root = "../" * depth if slug != "404" else "/"
        out = DIST / ("index.html" if slug == "index" else "404.html" if slug == "404" else f"{slug}/index.html")
        canonical = f"{SITE_URL}/" + ("" if slug == "index" else f"{slug}/")

        current = ' aria-current="page"'
        nav = "".join(
            f'<li><a href="{url_for(s, root)}"{current if s == slug else ""}>{label}</a></li>'
            for s, label in NAV if s != "request-a-quote")
        city_links = "".join(f'<li><a href="{root}service-areas/#{k}">{c}, FL</a></li>' for k, c in CITIES)

        ctx = {
            "root": root, "year": YEAR, "business_name": e(NAME), "legal_name": e(LEGAL),
            "location": e(LOCATION), "site_url": SITE_URL,
            "nav_items": nav, "footer_city_links": city_links,
            "contact_list": contact_list("contact-list"),
            "footer_contact": contact_list("footer__contact"),
            "social_links": social_list(),
            "contact_fallback": contact_fallback(),
            "contact_fallback_attr": e(contact_fallback()),
            "testimonials": testimonials_section(),
            "policy_date": e(POLICY_DATE) if POLICY_DATE else "[effective date to be set before launch]",
            "header_phone": (f'<a class="header__phone" href="tel:{e(PHONE_TEL)}">{e(PHONE)}</a>' if PHONE else ""),
            "quote_current": ' aria-current="page"' if slug == "request-a-quote" else "",
        }
        content = render(body, ctx)

        head_extra = []
        if meta.get("schema"):
            head_extra.append(schema(canonical))
        if CFG.get("google_site_verification"):
            head_extra.append(f'<meta name="google-site-verification" content="{e(CFG["google_site_verification"])}">')
        if PLAUSIBLE:
            head_extra.append(f'<script defer data-domain="{e(PLAUSIBLE)}" src="https://plausible.io/js/script.js"></script>')
        if meta.get("noindex"):
            head_extra.append('<meta name="robots" content="noindex">')

        ctx.update({
            "title": e(meta["title"]), "description": e(meta["description"]),
            "canonical": canonical, "og_image": f"{SITE_URL}/img/og-image.png",
            "head_extra": "\n  ".join(head_extra), "content": content,
            "body_class": meta.get("body_class", ""),
        })
        page = render((SRC / "layout.html").read_text(), ctx)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        if not meta.get("noindex"):
            sitemap.append((canonical, meta.get("priority", "0.7")))

    today = datetime.date.today().isoformat()
    urls = "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><priority>{p}</priority></url>\n" for u, p in sitemap)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /thank-you/\n\nSitemap: {SITE_URL}/sitemap.xml\n")

    # Security headers (Netlify reads dist/_headers)
    analytics_src = " https://plausible.io" if PLAUSIBLE else ""
    csp = ("default-src 'self'; "
           f"script-src 'self'{analytics_src}; connect-src 'self'{analytics_src}; "
           "style-src 'self'; img-src 'self' data:; font-src 'self'; "
           "form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests")
    (DIST / "_headers").write_text(
        "/*\n"
        f"  Content-Security-Policy: {csp}\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()\n"
        "  Strict-Transport-Security: max-age=31536000; includeSubDomains\n"
        "  X-Frame-Options: DENY\n"
        "/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/img/*\n  Cache-Control: public, max-age=604800\n"
        "/css/*\n  Cache-Control: public, max-age=86400, must-revalidate\n"
        "/js/*\n  Cache-Control: public, max-age=86400, must-revalidate\n")

    print(f"Built {len(pages)} pages into {DIST.relative_to(ROOT)}/")
    if missing:
        print("\nStill to provide before launch (hidden on the site until set in site.config.json):")
        for m in missing:
            print("  -", m)


if __name__ == "__main__":
    build()
