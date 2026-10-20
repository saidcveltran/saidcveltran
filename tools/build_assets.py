#!/usr/bin/env python3
"""Generate the hand-made SVG assets of the profile (hero, footer, cards, stack, placeholders).

Standard library only. Run from anywhere:  python -I tools/build_assets.py
"""
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Palette sampled from assets/logo.png (blue -> cyan -> green ribbon):
#   #0A38AC  #0270BB  #1ECDE1  #00E68A
THEMES = {
    "dark": dict(bg1="#050A14", bg2="#0A1424", border="#16263F", text="#EAF1FA", muted="#93A6BF",
                 dim="#5C708A", c1="#3F78FF", c2="#1AA0E8", c3="#1ECDE1", c4="#00E68A",
                 tile="#0D1828", grid="#1B2B45", glow="0.20"),
    "light": dict(bg1="#F8FBFE", bg2="#EAF3FA", border="#CFDDEA", text="#0B1B2E", muted="#44586F",
                  dim="#7A8DA3", c1="#0A38AC", c2="#0270BB", c3="#0A9DB5", c4="#00A874",
                  tile="#FFFFFF", grid="#D6E3EF", glow="0.12"),
}

FONT_CSS = (
    ".f{font-family:'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif}"
    ".m{font-family:ui-monospace,'Cascadia Code','SF Mono',Consolas,'Liberation Mono',Menlo,monospace}"
)
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def doc(w, h, uid, title, desc, defs, css, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="{uid}-t {uid}-d">\n'
        f'<title id="{uid}-t">{esc(title)}</title>\n<desc id="{uid}-d">{esc(desc)}</desc>\n'
        f"<defs>{defs}</defs>\n<style>{FONT_CSS}{css}{REDUCED}</style>\n{body}\n</svg>\n"
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def brand_gradient(t, gid="g", x2="1", y2="0"):
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{t["c1"]}"/><stop offset=".45" stop-color="{t["c3"]}"/>'
        f'<stop offset="1" stop-color="{t["c4"]}"/></linearGradient>'
    )


# ---------------------------------------------------------------- network motif
def network(t, cx, cy, R, rnd, node_r=7.0):
    k = 0.866
    pts = {
        "t": (0, -R), "ur": (k * R, -R / 2), "lr": (k * R, R / 2),
        "b": (0, R), "ll": (-k * R, R / 2), "ul": (-k * R, -R / 2), "c": (0, 0),
    }
    cols = {"t": t["c1"], "ul": t["c1"], "ll": t["c2"], "c": t["c3"],
            "ur": t["c4"], "lr": t["c4"], "b": t["c4"]}
    edges = [("t", "ur"), ("ur", "lr"), ("lr", "b"), ("b", "ll"), ("ll", "ul"), ("ul", "t"),
             ("ul", "ur"), ("ll", "lr"), ("c", "t"), ("c", "ur"), ("c", "lr"),
             ("c", "b"), ("c", "ll"), ("c", "ul")]
    out = [f'<g transform="translate({cx} {cy})"><g class="float">']
    out.append(f'<circle class="orbit o1" r="{R * 1.38:.0f}" fill="none" stroke="{t["c3"]}" '
               f'stroke-opacity=".35" stroke-width="1.2" stroke-dasharray="2 9"/>')
    out.append(f'<circle class="orbit o2" r="{R * 1.7:.0f}" fill="none" stroke="{t["c2"]}" '
               f'stroke-opacity=".25" stroke-width="1" stroke-dasharray="1 12"/>')
    # satellites
    sats = []
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(R * 1.25, R * 1.6)
        sats.append((r * math.cos(a), r * math.sin(a)))
    for i, (sx, sy) in enumerate(sats):
        near = min(("t", "ur", "lr", "b", "ll", "ul"),
                   key=lambda n: (pts[n][0] - sx) ** 2 + (pts[n][1] - sy) ** 2)
        px, py = pts[near]
        out.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{t["c2"]}" '
                   f'stroke-opacity=".22" stroke-width="1"/>')
        out.append(f'<circle class="tw" style="animation-delay:{i * 0.7:.1f}s" cx="{sx:.1f}" cy="{sy:.1f}" '
                   f'r="{rnd.choice([2, 2.5, 3]):.1f}" fill="{t["c3"]}"/>')
    for a, b in edges:
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="url(#gl)" stroke-width="1.6" stroke-opacity=".55"/>')
    for i, (a, b) in enumerate(edges):
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        out.append(f'<line class="flow" style="animation-delay:-{i * 0.35:.2f}s" x1="{x1:.1f}" y1="{y1:.1f}" '
                   f'x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["c3"]}" stroke-width="2" stroke-linecap="round"/>')
    for i, (name, (x, y)) in enumerate(pts.items()):
        r = node_r * (1.6 if name == "c" else 1.0)
        out.append(f'<circle class="halo" style="animation-delay:{i * 0.45:.2f}s" cx="{x:.1f}" cy="{y:.1f}" '
                   f'r="{r * 2.3:.1f}" fill="{cols[name]}" fill-opacity="{t["glow"]}"/>')
        out.append(f'<circle class="node" style="animation-delay:{i * 0.45:.2f}s" cx="{x:.1f}" cy="{y:.1f}" '
                   f'r="{r:.1f}" fill="{cols[name]}"/>')
    out.append("</g></g>")
    return "\n".join(out)


NET_CSS = (
    "@keyframes flow{to{stroke-dashoffset:-32}}"
    "@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.3)}}"
    "@keyframes halo{0%,100%{opacity:.35}50%{opacity:1}}"
    "@keyframes tw{0%,100%{opacity:.15}50%{opacity:.9}}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    "@keyframes spinr{to{transform:rotate(-360deg)}}"
    "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}"
    ".flow{stroke-dasharray:3 13;animation:flow 2.4s linear infinite}"
    ".node,.halo{transform-box:fill-box;transform-origin:center}"
    ".node{animation:pulse 3.2s ease-in-out infinite}"
    ".halo{animation:halo 3.2s ease-in-out infinite}"
    ".tw{animation:tw 4s ease-in-out infinite}"
    ".float{animation:float 8s ease-in-out infinite}"
    ".orbit.o1{animation:spin 60s linear infinite}"
    ".orbit.o2{animation:spinr 90s linear infinite}"
)


# ---------------------------------------------------------------- hero
TYPED = ["open data · BOE · JSON", "discord bots · /play · autoplay",
         "3D games · Godot", "animation tools · Blender"]


def hero(mode):
    t = THEMES[mode]
    W, H = 1200, 360
    rnd = random.Random(7)
    adv, fs = 13.2, 22
    slot = 4
    total = slot * len(TYPED)
    css = [NET_CSS,
           "@keyframes drift{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}"
           ".dot{animation:drift 7s ease-in-out infinite}",
           "@keyframes type{0%{width:0}7%{width:var(--w)}20%{width:var(--w)}25%{width:0}100%{width:0}}"
           "@keyframes cur{0%{transform:translateX(0);opacity:1}7%{transform:translateX(var(--w));opacity:1}"
           "20%{transform:translateX(var(--w));opacity:1}25%{transform:translateX(0);opacity:1}"
           "25.5%{opacity:0}100%{transform:translateX(0);opacity:0}}"
           "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:.1}}"
           ".clip{width:0;animation:type TOTALs steps(26) infinite}"
           ".cur{opacity:0;animation:cur TOTALs steps(26) infinite}"
           ".blink{animation:blink 1s steps(1) infinite}".replace("TOTAL", str(total)),
           ".clip.l0{width:var(--w)}"]
    defs = [brand_gradient(t),
            f'<linearGradient id="gl" gradientUnits="userSpaceOnUse" x1="-90" y1="-90" x2="90" y2="90">'
            f'<stop offset="0" stop-color="{t["c1"]}"/><stop offset=".5" stop-color="{t["c3"]}"/>'
            f'<stop offset="1" stop-color="{t["c4"]}"/></linearGradient>',
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg1"]}"/>'
            f'<stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>',
            f'<radialGradient id="gl1" cx="955" cy="180" r="330" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{t["c2"]}" stop-opacity="{t["glow"]}"/>'
            f'<stop offset="1" stop-color="{t["c2"]}" stop-opacity="0"/></radialGradient>',
            f'<radialGradient id="gl2" cx="140" cy="60" r="360" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{t["c1"]}" stop-opacity="{t["glow"]}"/>'
            f'<stop offset="1" stop-color="{t["c1"]}" stop-opacity="0"/></radialGradient>',
            f'<pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1.1" fill="{t["grid"]}"/></pattern>',
            '<clipPath id="card"><rect width="1200" height="360" rx="22"/></clipPath>']
    body = ['<g clip-path="url(#card)">',
            '<rect width="1200" height="360" fill="url(#bg)"/>',
            '<rect width="1200" height="360" fill="url(#dots)" opacity=".7"/>',
            '<rect width="1200" height="360" fill="url(#gl1)"/><rect width="1200" height="360" fill="url(#gl2)"/>']
    for i in range(16):
        x, y = rnd.uniform(40, 1160), rnd.uniform(24, 336)
        body.append(f'<circle class="dot" style="animation-delay:-{rnd.uniform(0, 7):.1f}s" cx="{x:.0f}" '
                    f'cy="{y:.0f}" r="{rnd.choice([1.5, 2, 2.5])}" fill="{t["c3"]}" opacity=".35"/>')
    body.append(network(t, 960, 182, 92, rnd))
    body.append(f'<text class="m" x="72" y="92" font-size="15" letter-spacing="3" fill="{t["c3"]}">~/aiskaron</text>')
    body.append(f'<text class="f" x="68" y="172" font-size="78" font-weight="800" letter-spacing="-1" '
                f'fill="url(#g)">saidcveltran</text>')
    body.append(f'<text class="f" x="72" y="216" font-size="22" font-weight="600" fill="{t["text"]}">'
                f'Desarrollo herramientas de datos abiertos, bots y juegos.</text>')
    body.append(f'<text class="f" x="72" y="244" font-size="17" fill="{t["muted"]}">'
                f'I build open-data tools, bots and games.</text>')
    body.append(f'<text class="m" x="72" y="299" font-size="{fs}" font-weight="700" fill="{t["c2"]}">$</text>')
    for i, line in enumerate(TYPED):
        w = len(line) * adv
        defs.append(f'<clipPath id="c{i}"><rect class="clip l{i}" style="--w:{w:.1f}px;animation-delay:{i * slot}s" '
                    f'x="100" y="272" height="40"/></clipPath>')
        body.append(f'<text class="m" x="100" y="299" font-size="{fs}" fill="{t["text"]}" '
                    f'textLength="{w:.1f}" lengthAdjust="spacing" clip-path="url(#c{i})">{esc(line)}</text>')
        body.append(f'<g class="cur l{i}" style="--w:{w:.1f}px;animation-delay:{i * slot}s">'
                    f'<rect class="blink" x="100" y="279" width="9" height="24" rx="2" fill="{t["c4"]}"/></g>')
    body.append(f'<rect x=".75" y=".75" width="1198.5" height="358.5" rx="21.5" fill="none" '
                f'stroke="{t["border"]}" stroke-width="1.5"/>')
    body.append("</g>")
    return doc(W, H, "hero",
               "saidcveltran, AIskaron projects",
               "Animated banner: saidcveltran. Desarrollo herramientas de datos abiertos, bots y juegos. "
               "I build open-data tools, bots and games. An animated network of nodes, like the AIskaron "
               "logo, and rotating lines: open data, Discord bots, 3D games, animation tools.",
               "".join(defs), "".join(css), "\n".join(body))


# ---------------------------------------------------------------- footer
def footer(mode):
    t = THEMES[mode]
    W, H = 1200, 150
    rnd = random.Random(11)
    P = 300
    defs = [brand_gradient(t),
            f'<linearGradient id="gl" gradientUnits="userSpaceOnUse" x1="-40" y1="-40" x2="40" y2="40">'
            f'<stop offset="0" stop-color="{t["c1"]}"/><stop offset=".5" stop-color="{t["c3"]}"/>'
            f'<stop offset="1" stop-color="{t["c4"]}"/></linearGradient>',
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["bg1"]}"/>'
            f'<stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>',
            f'<linearGradient id="wv" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["c1"]}"/>'
            f'<stop offset=".5" stop-color="{t["c3"]}"/><stop offset="1" stop-color="{t["c4"]}"/></linearGradient>',
            '<clipPath id="card"><rect width="1200" height="150" rx="22"/></clipPath>']
    css = [NET_CSS, "@keyframes wave{to{transform:translateX(300px)}}"
           ".w1{animation:wave 14s linear infinite}.w2{animation:wave 22s linear infinite}"
           ".w3{animation:wave 34s linear infinite}"]

    def wave(amp, phase, cy):
        pts = []
        x = -P
        while x <= W + P:
            y = cy + amp * math.sin(2 * math.pi * x / P + phase)
            pts.append(f"{x:.0f} {y:.1f}")
            x += 15
        return "M" + " L".join(pts)

    body = ['<g clip-path="url(#card)">', f'<rect width="1200" height="150" fill="url(#bg)"/>']
    for cls, amp, ph, cy, op, sw in (("w3", 16, 0.0, 96, .30, 2), ("w2", 12, 1.6, 104, .45, 2),
                                     ("w1", 9, 3.1, 112, .75, 2.4)):
        body.append(f'<path class="{cls}" d="{wave(amp, ph, cy)}" fill="none" stroke="url(#wv)" '
                    f'stroke-opacity="{op}" stroke-width="{sw}"/>')
    body.append(network(t, 150, 62, 30, rnd, node_r=3.2))
    body.append(network(t, 1050, 62, 30, rnd, node_r=3.2))
    body.append(f'<text class="f" x="600" y="64" text-anchor="middle" font-size="30" font-weight="800" '
                f'fill="url(#g)">saidcveltran</text>')
    body.append(f'<text class="f" x="600" y="90" text-anchor="middle" font-size="14" fill="{t["muted"]}">'
                f'Gracias por pasar · Thanks for stopping by</text>')
    body.append(f'<rect x=".75" y=".75" width="1198.5" height="148.5" rx="21.5" fill="none" '
                f'stroke="{t["border"]}" stroke-width="1.5"/></g>')
    return doc(W, H, "footer", "saidcveltran",
               "Animated footer with flowing waves and a small node network. "
               "Gracias por pasar. Thanks for stopping by.",
               "".join(defs), "".join(css), "\n".join(body))


# ---------------------------------------------------------------- cards
CARD_W, CARD_H = 480, 250

# status key -> (ES · EN, accent role)
CARDS = {
    "normawatch": dict(
        name="NormaWatch", status="PUBLICADO · PUBLISHED", scol="c4",
        es=["Actor gratuito de Apify: cada día, las nuevas disposiciones", "generales del BOE en JSON y tabla, con aviso opcional."],
        en=["Free Apify Actor: every day's new BOE general provisions", "as JSON and a table, with optional email/Telegram/Slack."],
        tags=["TypeScript", "Node.js", "Apify"], extra="v1.8.0"),
    "duckys": dict(
        name="DUCKYS", status="PRIVADO · PRIVATE", scol="orange",
        es=["Bot de música para Discord: comando /play, autoplay,", "muchos idiomas y panel web."],
        en=["Discord music bot: /play command, autoplay, many", "languages and a web panel."],
        tags=["Discord", "/play", "autoplay", "web panel"], extra=""),
    "aiskaron": dict(
        name="aiskaron.com", status="PRÓXIMAMENTE · COMING SOON", scol="c3",
        es=["Mi centro personal con todos los proyectos de AIskaron,", "en un solo sitio."],
        en=["My personal hub for all the AIskaron projects,", "in one place."],
        tags=["web", "hub"], extra=""),
    "robots-kinora": dict(
        name="Robots · Kinora", status="EN DESARROLLO · IN DEVELOPMENT", scol="c2",
        blocks=[("Robots", "Combate 3D en Godot: partes rompibles y un enemigo que aprende.",
                 "3D combat in Godot: breakable parts and an enemy that learns."),
                ("Kinora", "Plantilla open source para animar personajes en Blender.",
                 "Open-source template to animate characters in Blender.")],
        tags=[], extra=""),
}

DUCKYS = dict(navy="#012F44", deep="#011F2E", light="#0B4A66", white="#FBF7F2", orange="#FEA90E")


def card(key, mode):
    c = CARDS[key]
    t = THEMES[mode]
    d = DUCKYS
    duck = key == "duckys"
    if duck and mode == "dark":
        bg1, bg2, border, text, muted = d["navy"], d["deep"], d["light"], d["white"], "#A9C2CE"
        name_fill, accent, chip_bg, chip_tx = d["orange"], d["orange"], "#06384F", "#D5E4EB"
    elif duck:
        bg1, bg2, border, text, muted = d["white"], "#F3ECE1", "#E4D9C8", d["navy"], "#3B5B6B"
        name_fill, accent, chip_bg, chip_tx = d["navy"], d["orange"], "#EFE5D6", d["navy"]
    else:
        bg1, bg2, border, text, muted = t["bg1"], t["bg2"], t["border"], t["text"], t["muted"]
        name_fill, accent = "url(#g)", t["c3"]
        chip_bg = "#0E1B2F" if mode == "dark" else "#E8F1F8"
        chip_tx = t["text"]
    scol = {"orange": d["orange"] if mode == "dark" else "#B86F00"}.get(c["scol"]) or t[c["scol"]]
    ptext = scol
    defs = [brand_gradient(t),
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg1}"/>'
            f'<stop offset="1" stop-color="{bg2}"/></linearGradient>',
            f'<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{accent}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{accent}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient>',
            f'<clipPath id="cl"><rect width="{CARD_W}" height="{CARD_H}" rx="16"/></clipPath>']
    css = ["@keyframes shim{from{transform:translateX(0)}to{transform:translateX(640px)}}"
           ".shim{animation:shim 6s ease-in-out infinite}"]
    pw = len(c["status"]) * 7.2 + 30
    body = [f'<g clip-path="url(#cl)"><rect width="{CARD_W}" height="{CARD_H}" fill="url(#bg)"/>',
            f'<rect class="shim" x="-160" y="0" width="160" height="3" fill="url(#sh)"/>']
    body.append(f'<text class="f" x="28" y="56" font-size="26" font-weight="800" fill="{name_fill}">{esc(c["name"])}</text>')
    if c["extra"]:
        body.append(f'<text class="m" x="{CARD_W - 28}" y="54" text-anchor="end" font-size="13" fill="{muted}">{c["extra"]}</text>')
    body.append(f'<rect x="28" y="70" width="{pw:.0f}" height="22" rx="11" fill="{scol}" fill-opacity=".14" '
                f'stroke="{scol}" stroke-opacity=".7"/>')
    body.append(f'<circle cx="42" cy="81" r="3.2" fill="{scol}"/>')
    body.append(f'<text class="f" x="52" y="85" font-size="10.5" font-weight="700" letter-spacing=".6" '
                f'fill="{ptext}">{esc(c["status"])}</text>')
    if "blocks" in c:
        y = 126
        for label, es, en in c["blocks"]:
            body.append(f'<text class="f" x="28" y="{y}" font-size="14" font-weight="700" fill="{accent if duck else text}">{esc(label)}</text>')
            body.append(f'<text class="f" x="28" y="{y + 19}" font-size="12.5" fill="{text}">{esc(es)}</text>')
            body.append(f'<text class="f" x="28" y="{y + 36}" font-size="12" font-style="italic" fill="{muted}">{esc(en)}</text>')
            y += 68
    else:
        for i, line in enumerate(c["es"]):
            body.append(f'<text class="f" x="28" y="{124 + i * 19}" font-size="13.5" fill="{text}">{esc(line)}</text>')
        for i, line in enumerate(c["en"]):
            body.append(f'<text class="f" x="28" y="{176 + i * 18}" font-size="12.5" font-style="italic" fill="{muted}">{esc(line)}</text>')
        x = 28
        for tag in c["tags"]:
            w = len(tag) * 6.8 + 20
            body.append(f'<rect x="{x}" y="211" width="{w:.0f}" height="24" rx="6" fill="{chip_bg}" stroke="{border}"/>')
            body.append(f'<text class="m" x="{x + w / 2:.0f}" y="227" text-anchor="middle" font-size="11.5" fill="{chip_tx}">{esc(tag)}</text>')
            x += w + 8
    body.append(f'</g><rect x=".75" y=".75" width="{CARD_W - 1.5}" height="{CARD_H - 1.5}" rx="15.5" fill="none" '
                f'stroke="{border}" stroke-width="1.5"/>')
    if "blocks" in c:
        desc = " ".join(f"{b[0]}: {b[1]} {b[2]}" for b in c["blocks"])
    else:
        desc = " ".join(c["es"] + c["en"])
    return doc(CARD_W, CARD_H, "card", f'{c["name"]} ({c["status"]})', desc, "".join(defs), "".join(css), "\n".join(body))


# ---------------------------------------------------------------- stack
ICONS = [("typescript", "TypeScript", "#3178C6"), ("javascript", "JavaScript", "#F7DF1E"),
         ("nodedotjs", "Node.js", "#5FA04E"), ("python", "Python", "#3776AB"),
         ("godotengine", "Godot", "#478CBF"), ("blender", "Blender", "#E87D0D"),
         ("cloudflare", "Cloudflare", "#F38020"), ("apify", "Apify", "#2F6BFF"),
         ("git", "Git", "#F05032"), ("discord", "Discord", "#5865F2")]


def stack(mode):
    t = THEMES[mode]
    W, H = 830, 118
    step = W / len(ICONS)
    css = ["@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}"
           ".it{animation:rise .6s ease-out backwards}"]
    body = []
    for i, (slug, label, color) in enumerate(ICONS):
        cx = step * (i + 0.5)
        g = [f'<g class="it" style="animation-delay:{i * 0.08:.2f}s">',
             f'<rect x="{cx - 32:.1f}" y="8" width="64" height="64" rx="16" fill="{t["tile"]}" stroke="{t["border"]}" stroke-width="1.5"/>']
        p = ASSETS / "icons" / f"{slug}.svg"
        if p.exists():
            ds = re.findall(r'<path[^>]* d="([^"]+)"', p.read_text(encoding="utf-8"))
            g.append(f'<g transform="translate({cx - 15:.1f} 25) scale(1.25)" fill="{color}">'
                     + "".join(f'<path d="{d}"/>' for d in ds) + "</g>")
        else:  # Apify is not in simple-icons: plain monogram, no logo imitation
            g.append(f'<text class="m" x="{cx:.1f}" y="48" text-anchor="middle" font-size="22" font-weight="700" fill="{color}">Ap</text>')
        g.append(f'<text class="f" x="{cx:.1f}" y="96" text-anchor="middle" font-size="12.5" font-weight="600" fill="{t["muted"]}">{label}</text></g>')
        body.append("".join(g))
    return doc(W, H, "stack", "Stack",
               "Technologies: " + ", ".join(i[1] for i in ICONS) + ".", "", "".join(css), "\n".join(body))


# ---------------------------------------------------------------- placeholders
def placeholder_3d(mode):
    t = THEMES[mode]
    W, H = 830, 200
    rnd = random.Random(3)
    bars = []
    for i in range(36):
        h = rnd.choice([6, 10, 16, 26, 40, 56])
        x = 40 + i * 21
        bars.append(f'<rect x="{x}" y="{150 - h}" width="14" height="{h}" rx="2" fill="{t["c2"]}" opacity=".35"/>')
    body = (f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg1"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
            + "".join(bars) +
            f'<text class="f" x="415" y="40" text-anchor="middle" font-size="16" font-weight="700" fill="{t["text"]}">'
            f'Gráfico 3D de contribuciones · 3D contribution graph</text>'
            f'<text class="f" x="415" y="178" text-anchor="middle" font-size="13" fill="{t["muted"]}">'
            f'Se genera solo cada día · Generated automatically every day</text>')
    return doc(W, H, "p3d", "3D contribution graph (placeholder)",
               "Placeholder shown until the daily workflow generates the real 3D contribution graph.", "", "", body)


def placeholder_snake(mode):
    t = THEMES[mode]
    W, H = 830, 170
    rnd = random.Random(5)
    cells = []
    for c in range(53):
        for r in range(7):
            lvl = rnd.choice([0, 0, 0, 1, 1, 2])
            col = t["grid"] if lvl == 0 else t["c2"]
            op = "1" if lvl == 0 else str(0.25 * lvl + 0.1)
            cells.append(f'<rect x="{20 + c * 15}" y="{22 + r * 15}" width="11" height="11" rx="2" fill="{col}" opacity="{op}"/>')
    body = (f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg1"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
            + "".join(cells) +
            f'<text class="f" x="415" y="152" text-anchor="middle" font-size="13" fill="{t["muted"]}">'
            f'La serpiente aparece tras la primera ejecución · The snake appears after the first run</text>')
    return doc(W, H, "psnk", "Contribution snake (placeholder)",
               "Placeholder shown until the daily workflow generates the contribution snake.", "", "", body)


def main():
    for m in ("dark", "light"):
        write(ASSETS / f"hero-{m}.svg", hero(m))
        write(ASSETS / f"footer-{m}.svg", footer(m))
        write(ASSETS / f"stack-{m}.svg", stack(m))
        for k in CARDS:
            write(ASSETS / "cards" / f"{k}-{m}.svg", card(k, m))
    write(ROOT / "profile-3d-contrib" / "profile-night-green.svg", placeholder_3d("dark"))
    write(ROOT / "profile-3d-contrib" / "profile-green.svg", placeholder_3d("light"))
    write(ROOT / "snake" / "github-snake-dark.svg", placeholder_snake("dark"))
    write(ROOT / "snake" / "github-snake.svg", placeholder_snake("light"))
    print("ok")


if __name__ == "__main__":
    main()
