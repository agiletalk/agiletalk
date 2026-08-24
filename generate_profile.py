#!/usr/bin/env python3
"""Generate a neofetch-style GitHub profile SVG for agiletalk.

Usage:
    python3 generate_profile.py > profile.svg

- 실행 시 GitHub REST API에서 스탯(repos/stars/followers/uptime/top language)을
  직접 가져온다. GITHUB_TOKEN 환경변수가 있으면 사용(rate limit 완화), 없어도 동작.
- 의존성 없음(stdlib only) — GitHub Actions에서 pip install 불필요.
- API 실패 시 그대로 예외를 던진다. 낡은 데이터를 조용히 커밋하는 것보다
  Action이 빨갛게 실패하는 편이 낫기 때문. (— 왜냐면 신뢰는 투명성에서 온다)
"""
import html
import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

USERNAME = "agiletalk"

# ── GitHub API ──────────────────────────────────────────────────
def gh(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-readme",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 403 and e.headers.get("x-ratelimit-remaining") == "0":
            raise SystemExit(
                "GitHub API rate limit exceeded. "
                "Set GITHUB_TOKEN env var and retry "
                "(GitHub Actions provides it automatically).") from e
        raise


def fetch_stats():
    user = gh(f"/users/{USERNAME}")
    repos, page = [], 1
    while True:
        batch = gh(f"/users/{USERNAME}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(r["stargazers_count"] for r in repos)
    own = [r for r in repos if not r["fork"]]
    langs = {}
    for r in own:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
    top_lang, top_n = max(langs.items(), key=lambda x: x[1])

    created = datetime.strptime(
        user["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
    return {
        "repos": user["public_repos"],
        "stars": stars,
        "followers": user["followers"],
        "created": created,
        "top_lang": f"{top_lang} ({top_n}/{len(own)} repos)",
    }


def uptime_str(start, end=None):
    end = end or date.today()
    y, m, d = end.year - start.year, end.month - start.month, end.day - start.day
    if d < 0:
        m -= 1
        prev_last = date(end.year, end.month, 1) - timedelta(days=1)
        d += prev_last.day
    if m < 0:
        y -= 1
        m += 12
    def p(n, w):  # pluralize
        return f"{n} {w}{'' if n == 1 else 's'}"
    return f"{p(y, 'year')}, {p(m, 'month')}, {p(d, 'day')}"


# ── layout constants ────────────────────────────────────────────
FONT = "'DejaVu Sans Mono', Menlo, Consolas, monospace"
FS = 14            # font size
LH = 19            # line height
W_INFO = 58        # info column width in chars (dot-leader padding)
ART_X, INFO_X = 30, 348
TOP = 64           # first text baseline (below titlebar)
WIDTH, HEIGHT = 900, 534

# ── colors (GitHub dark terminal palette) ───────────────────────
C = {
    "green": "#3fb950", "yellow": "#d29922", "orange": "#db6d28",
    "red": "#f85149", "magenta": "#bc8cff", "blue": "#58a6ff",
    "cyan": "#39c5cf", "field": "#ffa657", "dots": "#484f58",
    "value": "#c9d1d9", "dim": "#8b949e", "bg": "#0d1117",
    "border": "#30363d", "titlebar": "#161b22",
}

# ── ASCII art: macOS neofetch apple, rainbow bands ──────────────
APPLE = [
    "                    'c.",
    "                 ,xNMM.",
    "               .OMMMMo",
    "               OMMM0,",
    "     .;loddo:' loolloddol;.",
    "   cKMMMMMMMMMMNWMMMMMMMMMM0:",
    " .KMMMMMMMMMMMMMMMMMMMMMMMWd.",
    " XMMMMMMMMMMMMMMMMMMMMMMMX.",
    ";MMMMMMMMMMMMMMMMMMMMMMMM:",
    ":MMMMMMMMMMMMMMMMMMMMMMMM:",
    ".MMMMMMMMMMMMMMMMMMMMMMMMX.",
    " kMMMMMMMMMMMMMMMMMMMMMMMMWd.",
    " .XMMMMMMMMMMMMMMMMMMMMMMMMMMk",
    "  .XMMMMMMMMMMMMMMMMMMMMMMMMK.",
    "    kMMMMMMMMMMMMMMMMMMMMMMd",
    "     ;KMMMMMMMWXXWMMMMMMMk.",
    "       .cooc,.    .,coo:.",
]
BAND = (["green"] * 4 + ["yellow"] * 3 + ["orange"] * 3 +
        ["red"] * 3 + ["magenta"] * 2 + ["blue"] * 2)

# Aquarium easter egg under the logo
FISH = [
    ("", "dim"),
    ("   ~~~~~~~~~~~~~~~~~~~~~~~~~", "cyan"),
    ("     ><((('>      <')))><", "blue"),
    ("   ~ agiletalk/Aquarium ~", "dots"),
]


# ── info column ─────────────────────────────────────────────────
def kv(f, v):
    return ("kv", f, v)


def sec(t):
    return ("sec", t)


BLANK = ("blank",)


def build_info(s):
    return [
        ("head", "chanju", "wantedlab"),
        ("sep",),
        kv("OS", "macOS, iOS 26"),
        kv("Uptime", uptime_str(s["created"])),
        kv("Host", "Wantedlab Inc."),
        kv("Kernel", "iOS Engineer / Agentic AI Developer"),
        kv("Shell", "zsh + Claude Code"),
        kv("IDE", "Xcode 26, Zed"),
        BLANK,
        kv("Languages.Programming", "Swift, Python, JavaScript"),
        kv("Languages.Computer", "SwiftUI, HTML, YAML, JSON"),
        kv("Languages.Real", "Korean, English"),
        BLANK,
        kv("Hobbies.Software", "Indie iOS apps, Swift CLIs"),
        kv("Hobbies.Terminal", "Aquarium, madang, commit-museum"),
        BLANK,
        sec("Contact"),
        kv("Blog", "agiletalk.github.io"),
        kv("Medium", "medium.com/@agiletalk"),
        kv("GitHub", "github.com/agiletalk"),
        BLANK,
        sec("GitHub Stats"),
        ("stats", [("Repos", str(s["repos"])), ("Stars", str(s["stars"])),
                   ("Followers", str(s["followers"]))]),
        kv("Top.Language", s["top_lang"]),
    ]


# ── svg helpers ─────────────────────────────────────────────────
def esc(s):
    return html.escape(s, quote=True)


def tspan(text, color, bold=False):
    w = ' font-weight="bold"' if bold else ""
    return f'<tspan fill="{C[color]}"{w}>{esc(text)}</tspan>'


def text_line(x, y, spans):
    return (f'<text x="{x}" y="{y}" xml:space="preserve" '
            f'font-family="{FONT}" font-size="{FS}">{spans}</text>')


def render(info_lines):
    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    out.append(
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="10" fill="{C["bg"]}" '
        f'stroke="{C["border"]}" stroke-width="1"/>')
    # terminal titlebar
    out.append(f'<path d="M1 11 Q1 1 11 1 H{WIDTH-11} Q{WIDTH-1} 1 '
               f'{WIDTH-1} 11 V34 H1 Z" fill="{C["titlebar"]}"/>')
    out.append(f'<line x1="1" y1="34" x2="{WIDTH-1}" y2="34" '
               f'stroke="{C["border"]}"/>')
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append(f'<circle cx="{22 + i * 20}" cy="18" r="6" fill="{col}"/>')
    out.append(text_line(WIDTH / 2 - 100, 23,
                         tspan("agiletalk / README.md", "dim")))

    # left: apple + fish
    y = TOP + 2 * LH
    for line, band in zip(APPLE, BAND):
        out.append(text_line(ART_X, y, tspan(line, band, bold=True)))
        y += LH
    y += LH
    for line, color in FISH:
        if line:
            out.append(text_line(ART_X, y, tspan(line, color)))
        y += LH

    # right: info column
    y = TOP
    for line in info_lines:
        kind = line[0]
        if kind == "blank":
            pass
        elif kind == "head":
            _, user, host = line
            out.append(text_line(INFO_X, y,
                       tspan(user, "green", True) + tspan("@", "value")
                       + tspan(host, "green", True)))
        elif kind == "sep":
            out.append(text_line(INFO_X, y, tspan("─" * 24, "dots")))
        elif kind == "sec":
            t = f"· {line[1]} "
            pad = "·" * (W_INFO - len(t))
            out.append(text_line(INFO_X, y,
                       tspan(t, "dim", True) + tspan(pad, "dots")))
        elif kind == "kv":
            _, f, v = line
            dots = "." * max(1, W_INFO - len(f) - len(v) - 2)
            out.append(text_line(INFO_X, y,
                       tspan(f, "field", True) + tspan(":", "dim")
                       + tspan(dots, "dots") + tspan(" " + v, "value")))
        elif kind == "stats":
            spans, first = "", True
            for f, v in line[1]:
                if not first:
                    spans += tspan("  |  ", "dots")
                spans += (tspan(f + ": ", "field", True)
                          + tspan(v, "cyan", True))
                first = False
            out.append(text_line(INFO_X, y, spans))
        y += LH

    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    print(render(build_info(fetch_stats())))
