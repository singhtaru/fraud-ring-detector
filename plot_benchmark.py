"""Phase 8: plot benchmark_results.csv as benchmark.svg (log-scale time axis).

Standard library only (matplotlib is unavailable on this machine).
Open the SVG in a browser, or insert it into Word/PowerPoint.
Usage: python plot_benchmark.py
"""
import csv
import math

rows = list(csv.DictReader(open("benchmark_results.csv")))
TIMEOUT_S = 300
W, H, L, R, T, B = 640, 420, 70, 150, 40, 60
depths = sorted({int(r["depth"]) for r in rows})
times = [float(r["median_seconds"]) for r in rows if r["status"] == "ok"]
lo = 10 ** math.floor(math.log10(min(times)))
hi = 10 ** math.ceil(math.log10(max(times + [TIMEOUT_S])))


def x(d):
    return L + (d - depths[0]) / (depths[-1] - depths[0]) * (W - L - R)


def y(t):
    return T + (math.log10(hi) - math.log10(t)) / (math.log10(hi) - math.log10(lo)) * (H - T - B)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'font-family="Segoe UI, Arial, sans-serif" font-size="12">',
       f'<rect width="{W}" height="{H}" fill="white"/>',
       f'<text x="{L}" y="22" font-size="15" font-weight="bold">'
       f'Cycle detection time vs hop depth (6,941 start accounts)</text>']
e = math.log10(lo)
while e <= math.log10(hi) + 1e-9:
    t = 10 ** e
    svg.append(f'<line x1="{L}" x2="{W - R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="#ddd"/>')
    svg.append(f'<text x="{L - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{t:g} s</text>')
    e += 1
for d in depths:
    svg.append(f'<text x="{x(d):.1f}" y="{H - B + 20}" text-anchor="middle">{d}</text>')
svg.append(f'<text x="{(L + W - R) / 2}" y="{H - 15}" text-anchor="middle">Hop depth</text>')
svg.append(f'<line x1="{L}" x2="{W - R}" y1="{y(TIMEOUT_S):.1f}" y2="{y(TIMEOUT_S):.1f}" '
           f'stroke="#999" stroke-dasharray="4 4"/>')
svg.append(f'<text x="{W - R + 6}" y="{y(TIMEOUT_S) + 4:.1f}" fill="#666">timeout ({TIMEOUT_S} s)</text>')

for i, (engine, colour, label) in enumerate([("neo4j", "#1f6feb", "Neo4j (Cypher)"),
                                             ("sqlite", "#d9480f", "SQLite (recursive CTE)")]):
    pts = [(int(r["depth"]), float(r["median_seconds"])) for r in rows
           if r["engine"] == engine and r["status"] == "ok"]
    if pts:
        svg.append(f'<polyline fill="none" stroke="{colour}" stroke-width="2.5" points="'
                   + " ".join(f"{x(d):.1f},{y(t):.1f}" for d, t in pts) + '"/>')
        svg += [f'<circle cx="{x(d):.1f}" cy="{y(t):.1f}" r="4" fill="{colour}"/>' for d, t in pts]
    for r in rows:
        if r["engine"] == engine and r["status"] == "timeout":
            svg.append(f'<text x="{x(int(r["depth"])):.1f}" y="{y(TIMEOUT_S) - 6:.1f}" '
                       f'text-anchor="middle" fill="{colour}" font-weight="bold">&#215;</text>')
    ly = T + 20 + i * 20
    svg.append(f'<line x1="{W - R + 6}" x2="{W - R + 26}" y1="{ly}" y2="{ly}" stroke="{colour}" stroke-width="2.5"/>')
    svg.append(f'<text x="{W - R + 30}" y="{ly + 4}">{label}</text>')

svg.append("</svg>")
open("benchmark.svg", "w").write("\n".join(svg))
print("Wrote benchmark.svg")
