"""Generate a GitHub-dark Language Stack SVG from public and private repositories."""

import html
import json
import os
import urllib.request

LANG_COLORS = {
    "Python": "#5594c8",
    "Dart": "#00B4AB",
    "C": "#8f8f8f",
    "C++": "#f34b7d",
    "C#": "#178600",
    "MATLAB": "#e26b3c",
    "Shell": "#89e051",
    "CMake": "#dc4141",
    "Makefile": "#427819",
    "Batchfile": "#C1F12E",
    "PowerShell": "#012456",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "Dockerfile": "#384d54",
}
DEFAULT_COLOR = "#58a6ff"


def gh_get(url: str, token: str) -> object:
    """Perform an authenticated GitHub REST API GET request."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "language-stack-svg-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_language_bytes(token: str, exclude_forks: bool = True) -> dict[str, int]:
    """Aggregate language byte counts across all owner repositories (public + private)."""
    totals: dict[str, int] = {}
    page = 1
    while True:
        repos = gh_get(
            f"https://api.github.com/user/repos?affiliation=owner&per_page=100&page={page}",
            token,
        )
        if not repos:
            break
        for repo in repos:
            if exclude_forks and repo.get("fork"):
                continue
            langs = gh_get(repo["languages_url"], token)
            for lang, count in langs.items():
                totals[lang] = totals.get(lang, 0) + int(count)
        if len(repos) < 100:
            break
        page += 1
    return totals


def render_svg(totals: dict[str, int], top_n: int = 5) -> str:
    """Render top-N languages into a GitHub-dark Language Stack SVG."""
    total_bytes = sum(totals.values())
    if total_bytes <= 0:
        raise RuntimeError("No language bytes found across repositories")
    ranked = sorted(totals.items(), key=lambda x: -x[1])[:top_n]

    rows_svg = []
    for idx, (lang, byte_count) in enumerate(ranked):
        pct = max(1, int(byte_count * 100 / total_bytes + 0.5))
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        y_center = 107 + idx * 32
        y_text = y_center + 5
        y_bar = y_center - 9
        bar_w = max(19, int(466 * (byte_count / total_bytes) + 0.5))
        delay_ms = idx * 95
        safe_lang = html.escape(lang)
        rows_svg.append(
            f"""    <g class="stack-row" style="animation-delay:{delay_ms}ms">
      <circle cx="54" cy="{y_center}" r="5" fill="{color}"/>
      <text x="72" y="{y_text}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="14" font-weight="800" fill="#e6edf3">{safe_lang}</text>
      <text x="306" y="{y_text}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="13" font-weight="850" fill="{color}" text-anchor="end">{pct}%</text>
      <rect x="330" y="{y_bar}" width="466" height="9" rx="4.5" fill="rgba(255,255,255,0.12)"/>
      <rect class="stack-bar" x="330" y="{y_bar}" width="{bar_w}" height="9" rx="4.5" fill="{color}" opacity="0.95"/>
    </g>"""
        )

    rows_block = "\n".join(rows_svg)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="860" height="280" viewBox="0 0 860 280" role="img" aria-label="Language Stack">
  <defs>
    <linearGradient id="ls-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="54%" stop-color="#161b22"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <radialGradient id="ls-orb-0" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.65"/>
      <stop offset="58%" stop-color="#58a6ff" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#58a6ff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="ls-orb-1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#39d353" stop-opacity="0.45"/>
      <stop offset="58%" stop-color="#39d353" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#39d353" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="ls-orb-2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#a371f7" stop-opacity="0.65"/>
      <stop offset="58%" stop-color="#a371f7" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#a371f7" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    .stack-row {{ animation: ls-fade 650ms ease-out both; }}
    .stack-bar {{ animation: ls-grow 1.1s ease-out both; transform-box: fill-box; transform-origin: left; }}
    .stack-cursor {{ animation: ls-blink 1.1s step-end infinite; }}
    @keyframes ls-fade {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes ls-grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes ls-blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
  </style>
  <rect width="860" height="280" rx="20" fill="url(#ls-bg)"/>
  <ellipse cx="138" cy="50" rx="206" ry="129" fill="url(#ls-orb-0)" opacity="0.65"/>
  <ellipse cx="654" cy="62" rx="241" ry="118" fill="url(#ls-orb-1)" opacity="0.5"/>
  <ellipse cx="499" cy="246" rx="310" ry="95" fill="url(#ls-orb-2)" opacity="0.4"/>
  <rect x="28" y="26" width="804" height="226" rx="20" fill="rgba(8,8,12,0.5)" stroke="#58a6ff" stroke-opacity="0.5"/>
  <text x="46" y="61" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="27" font-weight="850" letter-spacing="-0.4" fill="#e6edf3">Language Stack</text>
  <text x="48" y="84" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="13" font-weight="650" letter-spacing="1.1" fill="#8b949e">Repository-weighted technologies (public + private)</text>
  <text x="685" y="62" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="14" font-weight="750" fill="#58a6ff">&gt; stack.scan</text>
  <text class="stack-cursor" x="786" y="62" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="14" font-weight="850" fill="#58a6ff">_</text>
{rows_block}
  <rect x="0.5" y="0.5" width="859" height="279" rx="19.5" fill="none" stroke="#58a6ff" stroke-opacity="0.62"/>
</svg>
"""


def main() -> None:
    token = os.environ.get("LANG_STATS_TOKEN", "").strip()
    if not token:
        raise SystemExit("LANG_STATS_TOKEN environment variable is required")
    out_path = os.environ.get("OUTPUT_PATH", "dist/language-stack.svg")
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    totals = fetch_language_bytes(token)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render_svg(totals))


if __name__ == "__main__":
    main()
