#!/usr/bin/env python3
"""Draw the contribution heatmap (light and dark SVG) from the GitHub GraphQL API.

Standard library only. Reads the token from the GITHUB_TOKEN environment variable and never
prints or stores it. Usage:  GITHUB_TOKEN=... python3 tools/heatmap.py [login]
"""
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "saidcveltran"
OUT = Path(__file__).resolve().parent.parent / "assets"

QUERY = (
    "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
    "totalContributions weeks{contributionDays{date contributionCount}}}}}}"
)

THEMES = {
    "dark": dict(ramp=["#161B22", "#0E3A40", "#11636B", "#1A9AA6", "#3DD6E8"], text="#9198A1"),
    "light": dict(ramp=["#EFF2F5", "#B6E8EE", "#6CCBD6", "#1E9AA8", "#0B6E79"], text="#59636E"),
}
FONT = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
CELL, GAP, PAD, TOP = 12, 3, 4, 34


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-heatmap"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data or not data.get("data", {}).get("user"):
        raise SystemExit("GraphQL error: " + json.dumps(data.get("errors", "no user"))[:300])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def thresholds(counts):
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [1, 2, 3]
    return [nz[min(len(nz) - 1, math.floor(len(nz) * q))] for q in (0.25, 0.5, 0.75)]


def level(c, th):
    if c <= 0:
        return 0
    return 1 + sum(c > t for t in th)


def fmt(n):
    return f"{n:,}".replace(",", ".")


def render(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    th = thresholds(counts)
    width = PAD * 2 + len(weeks) * (CELL + GAP) - GAP
    height = TOP + 7 * (CELL + GAP) - GAP + 40
    label = f"{fmt(total)} contribución" if total == 1 else f"{fmt(total)} contribuciones"
    label += " en el último año"
    parts = []
    for wi, w in enumerate(weeks):
        for di, d in enumerate(w["contributionDays"]):
            lv = level(d["contributionCount"], th)
            x = PAD + wi * (CELL + GAP)
            y = TOP + di * (CELL + GAP)
            parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t["ramp"][lv]}"/>')
    ly = TOP + 7 * (CELL + GAP) + 22
    lx = width - PAD - (5 * (CELL + GAP) + 78 + 36)
    legend = [f'<text x="{lx}" y="{ly}" font-size="13" fill="{t["text"]}">Menos</text>']
    gx = lx + 46
    for i in range(5):
        legend.append(f'<rect x="{gx + i * (CELL + GAP)}" y="{ly - 11}" width="{CELL}" height="{CELL}" rx="2" fill="{t["ramp"][i]}"/>')
    legend.append(f'<text x="{gx + 5 * (CELL + GAP) + 3}" y="{ly}" font-size="13" fill="{t["text"]}">Más</text>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="t d" font-family="{FONT}">\n'
        f'<title id="t">{label}</title>\n'
        f'<desc id="d">Mapa de calor de las contribuciones de {LOGIN} en las últimas 52 semanas, en cinco niveles.</desc>\n'
        f'<text x="{PAD}" y="20" font-size="14" fill="{t["text"]}">{label}</text>\n'
        + "\n".join(parts) + "\n" + "\n".join(legend) + "\n</svg>\n"
    )
    return svg


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    cal = fetch(token)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"activity-{theme}.svg").write_text(render(cal, theme), encoding="utf-8", newline="\n")
    print("total", cal["totalContributions"], "weeks", len(cal["weeks"]))


if __name__ == "__main__":
    main()
