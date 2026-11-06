"""Generates the simplified Treasure Coast route map (src/partials/route-map.svg).

Coordinates are approximate real-world lat/lon values, projected with a simple
equirectangular projection. Re-run with:  python3 tools/generate_map.py
"""
from pathlib import Path

S = 1300
LON0, LAT0 = -80.50, 27.56
KX = 0.888  # cos(27.3 deg) so east-west distances aren't stretched


def p(lat, lon):
    return (round((lon - LON0) * KX * S, 1), round((LAT0 - lat) * S, 1))


def path(points, close=False):
    pts = [p(*pt) for pt in points]
    d = f"M{pts[0][0]} {pts[0][1]}"
    # Catmull-Rom -> cubic bezier for smooth coastlines
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (round(p1[0] + (p2[0] - p0[0]) / 6, 1), round(p1[1] + (p2[1] - p0[1]) / 6, 1))
        c2 = (round(p2[0] - (p3[0] - p1[0]) / 6, 1), round(p2[1] - (p3[1] - p1[1]) / 6, 1))
        d += f" C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {p2[0]} {p2[1]}"
    return d + (" Z" if close else "")


mainland = [(27.56, -80.356), (27.50, -80.334), (27.45, -80.318), (27.42, -80.307),
            (27.38, -80.289), (27.33, -80.264), (27.29, -80.246), (27.25, -80.228),
            (27.215, -80.214), (27.20, -80.206), (27.17, -80.192), (27.13, -80.172), (27.10, -80.158)]
north_island = [(27.56, -80.336), (27.52, -80.316), (27.475, -80.293)]
south_island = [(27.462, -80.289), (27.40, -80.256), (27.33, -80.221), (27.27, -80.196),
                (27.20, -80.171), (27.168, -80.157)]
jupiter_island = [(27.160, -80.152), (27.13, -80.137), (27.10, -80.123)]
river = [(27.203, -80.208), (27.196, -80.235), (27.200, -80.258), (27.22, -80.282),
         (27.25, -80.305), (27.28, -80.322), (27.31, -80.338), (27.345, -80.352)]
south_fork = [(27.197, -80.255), (27.17, -80.262), (27.135, -80.272)]


def island(points, width=0.011):
    inner = [(lat, lon - width) for lat, lon in reversed(points)]
    return path(points + inner, close=True)


cities = {
    "fort-pierce": ("Fort Pierce", 27.4467, -80.333, "start"),
    "port-st-lucie": ("Port St. Lucie", 27.2730, -80.3582, "end"),
    "jensen-beach": ("Jensen Beach", 27.2545, -80.240, "start"),
    "stuart": ("Stuart", 27.1975, -80.2528, "end"),
}
xy = {k: p(v[1], v[2]) for k, v in cities.items()}
fp, psl, jb, st = xy["fort-pierce"], xy["port-st-lucie"], xy["jensen-beach"], xy["stuart"]
route = (f"M{fp[0]} {fp[1]} C{fp[0]-30} {fp[1]+80} {psl[0]+40} {psl[1]-90} {psl[0]} {psl[1]} "
         f"C{psl[0]-20} {psl[1]+40} {st[0]-60} {st[1]-10} {st[0]} {st[1]} "
         f"C{st[0]+40} {st[1]+8} {jb[0]-10} {jb[1]+40} {jb[0]} {jb[1]}")

nodes = []
for key, (name, lat, lon, anchor) in cities.items():
    x, y = xy[key]
    home = key == "port-st-lucie"
    dx = -16 if anchor == "end" else 16
    label_y = y + 5
    nodes.append(
        f'<a class="map-node{" map-node--home" if home else ""}" href="{{{{root}}}}service-areas/#{key}" '
        f'aria-label="{name} service area details">'
        + (f'<circle class="map-node__halo" cx="{x}" cy="{y}" r="16"/>' if home else "")
        + f'<circle class="map-node__dot" cx="{x}" cy="{y}" r="{8 if home else 6}"/>'
        f'<text class="map-node__label" x="{x + dx}" y="{label_y}" text-anchor="{anchor}">{name}</text>'
        + (f'<text class="map-node__sub" x="{x + dx}" y="{label_y + 17}" text-anchor="{anchor}">Home base</text>' if home else "")
        + "</a>"
    )

W, H = 470, 600
ox, oy = p(27.37, -80.185)
lx, ly = p(27.375, -80.262)
svg = f'''<svg class="route-map" data-animate viewBox="0 0 {W} {H}" role="group" aria-labelledby="map-title map-desc" xmlns="http://www.w3.org/2000/svg">
  <title id="map-title">Blue Route Logistics service area map</title>
  <desc id="map-desc">Simplified map of Florida's Treasure Coast showing the four cities we serve: Fort Pierce, Port St. Lucie, Jensen Beach and Stuart, between the Indian River Lagoon and the Atlantic Ocean.</desc>
  <defs>
    <radialGradient id="map-fade-g" cx="50%" cy="50%" r="62%">
      <stop offset="62%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/>
    </radialGradient>
    <mask id="map-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <rect width="{W}" height="{H}" fill="url(#map-fade-g)"/>
    </mask>
  </defs>
  <g class="map-geo" aria-hidden="true" mask="url(#map-fade)">
    <path class="map-land" d="{path(mainland)} L0 {H} L0 0 Z"/>
    <path class="map-island" d="{island(north_island)}"/>
    <path class="map-island" d="{island(south_island)}"/>
    <path class="map-island" d="{island(jupiter_island)}"/>
    <path class="map-river" d="{path(river)}"/>
    <path class="map-river" d="{path(south_fork)}"/>
    <path class="map-coast" d="{path(mainland)}"/>
    <text class="map-water" x="{ox}" y="{oy}" transform="rotate(-62 {ox} {oy})">Atlantic Ocean</text>
    <text class="map-water map-water--small" x="{lx}" y="{ly}" transform="rotate(-58 {lx} {ly})">Indian River Lagoon</text>
  </g>
  <g class="map-north" aria-hidden="true" transform="translate(420 60)"><path d="M0 -14 L6 6 L0 2 L-6 6 Z"/><text y="22" text-anchor="middle">N</text></g>
  <path class="map-route map-route--base" d="{route}" aria-hidden="true"/>
  <path class="map-route map-route--draw" d="{route}" pathLength="1" aria-hidden="true"/>
  {"".join(nodes)}
</svg>
'''

out = Path(__file__).resolve().parent.parent / "src" / "partials" / "route-map.svg"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(svg)
print("wrote", out)
