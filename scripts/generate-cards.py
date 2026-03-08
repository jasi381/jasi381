#!/usr/bin/env python3
"""Generate GitHub profile SVG cards — stats, top languages, and repo pins."""

import json
import os
import ssl
import urllib.request
from collections import defaultdict

# Handle SSL cert issues on macOS
SSL_CTX = ssl.create_default_context()
try:
    import certifi
    SSL_CTX.load_verify_locations(certifi.where())
except ImportError:
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE

USERNAME = "jasi381"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "assets", "generated")

# ── Theme ────────────────────────────────────────────────────────────────────
BG = "#0A0E14"
BORDER = "#1B2430"
PRIMARY = "#2ECC71"
ACCENT = "#F0A500"
TEXT = "#E6EDF3"
MUTED = "#7D8590"

# ── Language colors ──────────────────────────────────────────────────────────
LANG_COLORS = {
    "Kotlin": "#A97BFF",
    "Java": "#B07219",
    "Dart": "#00B4AB",
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "C++": "#F34B7D",
    "Go": "#00ADD8",
}

PINNED_REPOS = [
    ("DownloadManager", "AES-256 encrypted video streaming library with HLS/DASH and adaptive bitrate"),
    ("audio-player-compose", "Audio player component built with Jetpack Compose"),
    ("ImageLoader", "Custom image loading library written in Kotlin"),
    ("SharedTransitionElement", "Shared element transitions in Jetpack Compose"),
]

# ── GitHub API ───────────────────────────────────────────────────────────────

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    with urllib.request.urlopen(req, context=SSL_CTX) as r:
        return json.loads(r.read())


def fetch_data():
    user = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos?per_page=100&type=owner")

    total_stars = sum(r["stargazers_count"] for r in repos)
    total_forks = sum(r["forks_count"] for r in repos)

    # Aggregate languages
    langs = defaultdict(int)
    for r in repos:
        if r["fork"]:
            continue
        try:
            repo_langs = api(f"/repos/{USERNAME}/{r['name']}/languages")
            for lang, bytes_ in repo_langs.items():
                langs[lang] += bytes_
        except Exception:
            pass

    # Sort languages by bytes
    sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
    total_bytes = sum(b for _, b in sorted_langs) or 1
    top_langs = [(name, bytes_ / total_bytes * 100) for name, bytes_ in sorted_langs[:6]]

    # Per-repo data for pins
    pin_data = []
    for repo_name, desc in PINNED_REPOS:
        try:
            r = api(f"/repos/{USERNAME}/{repo_name}")
            pin_data.append({
                "name": repo_name,
                "desc": desc,
                "lang": r.get("language", "Kotlin") or "Kotlin",
                "stars": r["stargazers_count"],
                "forks": r["forks_count"],
            })
        except Exception:
            pin_data.append({
                "name": repo_name, "desc": desc,
                "lang": "Kotlin", "stars": 0, "forks": 0,
            })

    return {
        "followers": user["followers"],
        "public_repos": user["public_repos"],
        "total_stars": total_stars,
        "total_forks": total_forks,
        "top_langs": top_langs,
        "pins": pin_data,
    }


# ── SVG Generators ───────────────────────────────────────────────────────────

def svg_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_stats_card(data):
    rows = [
        ("M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z",
         "Total Stars", str(data["total_stars"])),
        ("M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8.5V1.5z",
         "Public Repos", str(data["public_repos"])),
        ("M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z",
         "Total Forks", str(data["total_forks"])),
        ("M2 5.5a3.5 3.5 0 115.898 2.549 5.507 5.507 0 013.034 4.084.75.75 0 11-1.482.235 4.001 4.001 0 00-7.9 0 .75.75 0 01-1.482-.236A5.507 5.507 0 013.102 8.05 3.49 3.49 0 012 5.5zM11 4a.75.75 0 100 1.5 1.5 1.5 0 01.666 2.844.75.75 0 00-.416.672v.352a.75.75 0 00.574.73c1.2.289 2.162 1.2 2.522 2.372a.75.75 0 101.434-.44 5.01 5.01 0 00-2.56-3.012A3 3 0 0011 4z",
         "Followers", str(data["followers"])),
    ]

    row_items = ""
    for i, (icon_path, label, value) in enumerate(rows):
        y = 60 + i * 32
        row_items += f"""
    <g transform="translate(25, {y})">
      <path fill="{ACCENT}" d="{icon_path}"/>
      <text x="28" y="13" fill="{MUTED}" font-size="14" font-family="'Segoe UI',Ubuntu,sans-serif">{label}</text>
      <text x="425" y="13" fill="{TEXT}" font-size="14" font-weight="600" font-family="'Segoe UI',Ubuntu,sans-serif" text-anchor="end">{value}</text>
    </g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="460" height="195" viewBox="0 0 460 195">
  <rect width="460" height="195" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
  <text x="25" y="36" fill="{PRIMARY}" font-size="18" font-weight="600" font-family="'Segoe UI',Ubuntu,sans-serif">GitHub Stats</text>
  <text x="435" y="36" fill="{MUTED}" font-size="13" font-family="'Segoe UI',Ubuntu,sans-serif" text-anchor="end">{USERNAME}</text>
  {row_items}
</svg>"""


def make_top_langs_card(top_langs):
    if not top_langs:
        return ""

    bar_width = 410
    bar_y = 55
    rows_needed = (len(top_langs) + 1) // 2
    card_h = 55 + 20 + rows_needed * 28 + 20

    # Progress bar segments
    bar_segments = ""
    offset = 0
    for name, pct in top_langs:
        color = LANG_COLORS.get(name, "#8B8B8B")
        w = max(pct / 100 * bar_width, 2)
        bar_segments += f'    <rect x="{25 + offset}" y="{bar_y}" width="{w}" height="8" rx="1.5" fill="{color}"/>\n'
        offset += w

    # Language labels
    labels = ""
    col = 0
    row = 0
    for i, (name, pct) in enumerate(top_langs):
        color = LANG_COLORS.get(name, "#8B8B8B")
        x = 25 + col * 205
        y = bar_y + 34 + row * 28
        labels += f"""    <g transform="translate({x}, {y})">
      <circle cx="6" cy="6" r="6" fill="{color}"/>
      <text x="18" y="10" fill="{MUTED}" font-size="12" font-family="'Segoe UI',Ubuntu,sans-serif">{svg_escape(name)}</text>
      <text x="130" y="10" fill="{TEXT}" font-size="12" font-weight="600" font-family="'Segoe UI',Ubuntu,sans-serif">{pct:.1f}%</text>
    </g>\n"""
        col += 1
        if col >= 2:
            col = 0
            row += 1

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{int(card_h)}" viewBox="0 0 460 {int(card_h)}">
  <rect width="460" height="{int(card_h)}" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
  <text x="25" y="36" fill="{PRIMARY}" font-size="18" font-weight="600" font-family="'Segoe UI',Ubuntu,sans-serif">Most Used Languages</text>
  <rect x="25" y="{bar_y}" width="{bar_width}" height="8" rx="4" fill="{BORDER}"/>
{bar_segments}
{labels}
</svg>"""


def make_pin_card(repo):
    name = svg_escape(repo["name"])
    desc = svg_escape(repo["desc"])
    lang = repo["lang"]
    lang_color = LANG_COLORS.get(lang, "#8B8B8B")
    stars = repo["stars"]
    forks = repo["forks"]

    # Truncate description to ~60 chars per line, max 2 lines
    words = desc.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 > 55 and current:
            lines.append(current)
            current = w
            if len(lines) >= 2:
                break
        else:
            current = f"{current} {w}".strip() if current else w
    if current and len(lines) < 2:
        lines.append(current)
    if len(lines) == 2 and len(desc) > sum(len(l) for l in lines):
        lines[1] = lines[1][:52] + "..."

    desc_lines = ""
    for j, line in enumerate(lines):
        desc_lines += f'  <text x="25" y="{62 + j * 18}" fill="{MUTED}" font-size="12" font-family=\'Segoe UI\',Ubuntu,sans-serif">{line}</text>\n'

    # Book icon
    book_icon = "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8.5V1.5z"
    # Star icon
    star_icon = "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"
    # Fork icon
    fork_icon = "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="130" viewBox="0 0 400 130">
  <rect width="400" height="130" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
  <g transform="translate(25, 20)">
    <path fill="{MUTED}" d="{book_icon}"/>
    <text x="22" y="13" fill="{PRIMARY}" font-size="14" font-weight="600" font-family="'Segoe UI',Ubuntu,sans-serif">{name}</text>
  </g>
{desc_lines}
  <g transform="translate(25, 108)">
    <circle cx="5" cy="0" r="5" fill="{lang_color}"/>
    <text x="15" y="4" fill="{MUTED}" font-size="12" font-family="'Segoe UI',Ubuntu,sans-serif">{lang}</text>
    <g transform="translate(90, -8)">
      <path fill="{MUTED}" d="{star_icon}"/>
      <text x="20" y="12" fill="{MUTED}" font-size="12" font-family="'Segoe UI',Ubuntu,sans-serif">{stars}</text>
    </g>
    <g transform="translate(140, -8)">
      <path fill="{MUTED}" d="{fork_icon}"/>
      <text x="20" y="12" fill="{MUTED}" font-size="12" font-family="'Segoe UI',Ubuntu,sans-serif">{forks}</text>
    </g>
  </g>
</svg>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT, exist_ok=True)

    print("Fetching GitHub data...")
    data = fetch_data()

    print("Generating stats card...")
    with open(os.path.join(OUTPUT, "stats.svg"), "w") as f:
        f.write(make_stats_card(data))

    print("Generating top languages card...")
    with open(os.path.join(OUTPUT, "top-langs.svg"), "w") as f:
        f.write(make_top_langs_card(data["top_langs"]))

    print("Generating pin cards...")
    for pin in data["pins"]:
        filename = f"pin-{pin['name'].lower()}.svg"
        with open(os.path.join(OUTPUT, filename), "w") as f:
            f.write(make_pin_card(pin))
        print(f"  -> {filename}")

    print("Done!")


if __name__ == "__main__":
    main()
