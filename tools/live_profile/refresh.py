"""Regenerate every live asset of the profile README test bench.

Usage: python3 -m live_profile.refresh   (run from the tools directory)

A file is written only when its content changed once the refresh timestamp is ignored, and the clock
is floored to the UTC day for geometry, so a scheduled run that finds nothing new makes no commit.
A source that is unavailable (the Duckys home page) keeps the last version of its card.
"""
from __future__ import annotations

import sys

from . import config
from .duckys_figures import fetch_figures
from .github_data import fetch_repos, utc_now
from .page_blocks import replace_block, write_if_changed
from .render_banner import render_banner
from .language_stats import load_languages
from .render_duckys_card import render_duckys_card
from .render_languages import icon_name, render_language_icon, render_language_row, split_by_icon
from .render_resma_card import render_resma_card
from .render_repo_card import card_name, render_repo_card, render_repo_cards_html
from .render_socials import GROUPS, button_name, group_label_name, render_button, render_group_label, render_social_links
from .render_title import render_title
from .svg_common import slug

REPO_LIMIT = 6
TITLES = ("Projects", "Languages", "Find me", "Ask")
BANNER_FOREGROUND = config.ROOT / "assets" / "profile-banner-foreground.webp"
DUCKYS_MARK = config.ROOT / "tools" / "art" / "duckys-mark.webp"


def main() -> int:
    clock = utc_now()
    day = clock.replace(hour=0, minute=0, second=0, microsecond=0)
    repos = fetch_repos(config.USER, limit=REPO_LIMIT, exclude=config.EXCLUDED_REPOS)
    figures = fetch_figures()
    if figures is None:
        print("warning: Duckys figures unavailable; the Duckys card keeps its last version", file=sys.stderr)
    assets = config.ROOT / "assets"
    languages, without_icon = split_by_icon(load_languages(config.LANGUAGES_FILE))
    if without_icon:
        print(f"warning: no vendored logo for {', '.join(without_icon)}; left out of the Languages row", file=sys.stderr)
    changed = [
        write_if_changed(assets / "profile-banner.svg", render_banner(repos, BANNER_FOREGROUND)),
        figures is not None and write_if_changed(assets / "duckys-card.svg", render_duckys_card(figures.rounded(), clock, DUCKYS_MARK)),
        write_if_changed(assets / "resma-card.svg", render_resma_card()),
        *[write_if_changed(assets / f"title-{slug(text)}.svg", render_title(text)) for text in TITLES],
        *[write_if_changed(assets / card_name(repo), render_repo_card(repo, day)) for repo in repos],
        replace_block(config.PAGE, "repos", render_repo_cards_html(repos, config.USER, config.ASSETS_URL)),
        *[write_if_changed(assets / icon_name(name), render_language_icon(name)) for name in languages],
        replace_block(config.PAGE, "languages", render_language_row(languages, config.ASSETS_URL)),
        *[write_if_changed(assets / button_name(link), render_button(link)) for _, _, links in GROUPS for link in links],
        *[write_if_changed(assets / group_label_name(title), render_group_label(title, note)) for title, note, _ in GROUPS],
        replace_block(config.PAGE, "socials", render_social_links(config.ASSETS_URL)),
    ]
    print("changed" if any(changed) else "unchanged", f"({len(repos)} repositories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
