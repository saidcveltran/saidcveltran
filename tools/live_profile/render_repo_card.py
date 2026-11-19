"""One small card per public repository: name, latest version, release date, description, language, last push.

Borderless and square: a faint tinted tile with an accent bar on top, where a glint travels along the bar.
Every card is its own image and carries a transparent gutter on the right, so a row of cards reads as
separate tiles. The description is the one the repository itself publishes, shortened to two lines.
"""
from __future__ import annotations

from html import escape

from .github_data import Repo
from .svg_common import DISPLAY_ADVANCE, clip, document, short_date, slug

TILE_WIDTH, GUTTER, HEIGHT = 252, 20, 176
WIDTH = TILE_WIDTH + GUTTER
PADDING = 18
NAME_SIZE = 18
NAME_LIMIT = int((TILE_WIDTH - 2 * PADDING) // (NAME_SIZE * DISPLAY_ADVANCE))
DESCRIPTION_CHARS, DESCRIPTION_LINES = 31, 2
CSS = f"""
.tile {{ fill: #3fb950; opacity: .07; }}
.glint {{ fill: #ffffff; opacity: .55; animation: glint 5.5s cubic-bezier(.6, 0, .4, 1) infinite; }}
@keyframes glint {{ from {{ transform: translateX(-70px); }} to {{ transform: translateX({TILE_WIDTH}px); }} }}
.rise {{ animation: rise .6s ease-out backwards; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} }}
@media (prefers-color-scheme: light) {{ .tile {{ fill: #1a7f37; opacity: .08; }} }}
"""


def wrap(text: str, width: int, lines: int) -> list[str]:
    """Word-wrap into at most `lines` lines of `width` characters; what does not fit ends with an ellipsis."""
    words, rows, current = text.split(), [], ""
    for word in words:
        word = clip(word, width)
        if current and len(current) + 1 + len(word) > width:
            rows.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        rows.append(current)
    if len(rows) > lines:
        rows = rows[:lines]
        last = rows[-1]
        rows[-1] = (last if len(last) < width else last[: width - 1]).rstrip() + "…"
    return rows


def card_name(repo: Repo) -> str:
    return f"repo-{slug(repo.name)}.svg"


def render_repo_card(repo: Repo, now) -> str:
    right = TILE_WIDTH - PADDING
    latest = repo.latest
    version = (f'<text class="accent display rise" x="{PADDING}" y="80" font-size="30">{escape(clip(latest.tag, 11))}</text>'
               f'<text class="muted rise" x="{PADDING}" y="99" font-size="11.5">released {short_date(latest.published)}</text>') if latest else \
              f'<text class="muted display rise" x="{PADDING}" y="80" font-size="18">no release yet</text>'
    state = "NEW" if repo.is_new(now) else repo.state(now)
    description = "".join(f'<text class="muted" x="{PADDING}" y="{122 + index * 16}" font-size="12">{escape(line)}</text>'
                          for index, line in enumerate(wrap(repo.description, DESCRIPTION_CHARS, DESCRIPTION_LINES)))
    footer_y = HEIGHT - 14
    body = [
        f'<rect class="tile" x="0" y="0" width="{TILE_WIDTH}" height="{HEIGHT}"/>',
        f'<rect class="accent" x="0" y="0" width="{TILE_WIDTH}" height="3"/>',
        f'<svg x="0" y="0" width="{TILE_WIDTH}" height="3" viewBox="0 0 {TILE_WIDTH} 3"><rect class="glint" style="animation-delay:-{(len(repo.name) * 0.7) % 5.5:.1f}s" x="0" y="0" width="70" height="3"/></svg>',
        f'<text class="ink display" x="{PADDING}" y="38" font-size="{NAME_SIZE}">{escape(clip(repo.name, NAME_LIMIT))}</text>',
        f'<text class="{"accent" if state in ("NEW", "ACTIVE") else "muted"}" x="{right}" y="20" font-size="10" letter-spacing="1.4" text-anchor="end">{state}</text>',
        version, description,
    ]
    if repo.language:
        body.append(f'<rect class="accent" x="{PADDING}" y="{footer_y - 8}" width="8" height="8"/>'
                    f'<text class="ink" x="{PADDING + 14}" y="{footer_y}" font-size="11.5">{escape(repo.language)}</text>')
    body.append(f'<text class="muted" x="{right}" y="{footer_y}" font-size="11.5" text-anchor="end">pushed {short_date(repo.pushed)}</text>')
    return document(HEIGHT, f"{repo.name}: {latest.tag if latest else 'no release yet'}", "\n".join(body), CSS, width=WIDTH, framed=False)


def render_repo_cards_html(repos: list[Repo], user: str, assets_url: str) -> str:
    """The row of cards for the README; each card links to its repository."""
    links = [f'<a href="https://github.com/{user}/{escape(repo.name)}"><img src="{assets_url}/{card_name(repo)}" '
             f'alt="{escape(repo.name)}: {escape(repo.latest.tag if repo.latest else "no release yet")}" width="{WIDTH}"></a>' for repo in repos]
    return "<p>\n" + "\n".join(links) + "\n</p>" if links else ""
