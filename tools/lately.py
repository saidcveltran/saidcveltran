#!/usr/bin/env python3
"""Fill the "Últimamente" / "Lately" list of README.md from the public GitHub REST API.

Standard library only. Reads the token from the GITHUB_TOKEN environment variable, sends it only in
the Authorization header and never prints it. Only public data is used.
Usage:  GITHUB_TOKEN=... python3 tools/lately.py [login]
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "saidcveltran"
README = Path(__file__).resolve().parent.parent / "README.md"
LIMIT = 5
API = "https://api.github.com"
MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|~>])")
LABELS = {
    "es": ("Versión", "PR aceptado en"),
    "en": ("Release", "Merged PR to"),
}


def get(path, token, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profile-lately",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(text):
    """Escape a title for Markdown and inline HTML."""
    text = " ".join(str(text).split())
    return MD_SPECIAL.sub(r"\\\1", html.escape(text, quote=False))


def short(text, n=60):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def releases(token):
    """Latest non-draft, non-prerelease release of each public, non-fork, non-archived repo."""
    repos = get(f"/users/{LOGIN}/repos", token, {"type": "owner", "per_page": 100})
    found = []
    for repo in repos:
        if repo.get("private") or repo.get("fork") or repo.get("archived"):
            continue
        rels = get(f"/repos/{repo['full_name']}/releases", token, {"per_page": 10})
        rels = [r for r in rels if not r.get("draft") and not r.get("prerelease") and r.get("published_at")]
        if rels:
            rel = max(rels, key=lambda r: r["published_at"])
            found.append((rel["published_at"], "release", repo["name"], rel["tag_name"], rel["html_url"]))
    return found


def pulls(token):
    q = f"is:pr is:merged is:public author:{LOGIN} -user:{LOGIN}"
    data = get("/search/issues", token, {"q": q, "sort": "updated", "order": "desc", "per_page": 30})
    found = []
    for it in data.get("items", []):
        merged = (it.get("pull_request") or {}).get("merged_at") or it.get("closed_at")
        if not merged:
            continue
        repo = it["repository_url"].rsplit("/repos/", 1)[-1]
        found.append((merged, "pr", repo, it["number"], it["html_url"], it["title"]))
    return found


def render(items, lang):
    rel_label, pr_label = LABELS[lang]
    lines = []
    for it in items:
        date = it[0][:10]
        if it[1] == "release":
            _, _, name, tag, url = it
            lines.append(f"- {rel_label} [{esc(name)} {esc(tag)}]({url}) · {date}")
        else:
            _, _, repo, num, url, title = it
            lines.append(f"- {pr_label} [{esc(repo)}\\#{num}]({url}): {esc(short(title))} · {date}")
    return lines


def fill(text, name, lines):
    body = "\n".join(lines) if lines else "- –"
    pattern = re.compile(rf"(<!-- {name}:start -->)\n.*?\n?(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"markers for {name} not found")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    items = sorted(releases(token) + pulls(token), key=lambda i: i[0], reverse=True)[:LIMIT]
    text = README.read_text(encoding="utf-8")
    for lang in LABELS:
        text = fill(text, f"lately-{lang}", render(items, lang))
    README.write_text(text, encoding="utf-8", newline="\n")
    print("items", len(items))


if __name__ == "__main__":
    main()
