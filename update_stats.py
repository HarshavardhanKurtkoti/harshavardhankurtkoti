#!/usr/bin/env python3
"""
update_stats.py — Fetches live GitHub data for HarshavardhanKurtkoti
and injects it into the profile SVG templates.

Usage:
  python update_stats.py                     # uses GITHUB_TOKEN env var
  python update_stats.py --token YOUR_TOKEN  # explicit token
"""

import os
import re
import json
import math
import argparse
import urllib.request
import urllib.error

USERNAME = "HarshavardhanKurtkoti"

LANG_COLORS = {
    "Python":     "#ff7a59",
    "TypeScript": "#3178c6",
    "JavaScript": "#f7df1e",
    "HTML":       "#e34f26",
    "CSS":        "#563d7c",
    "PHP":        "#777bb4",
    "Jupyter Notebook": "#da5b0b",
    "Shell":      "#89e051",
    "C":          "#555555",
    "C++":        "#f34b7d",
    "Go":         "#00add8",
    "Rust":       "#dea584",
    "Java":       "#b07219",
    "Kotlin":     "#A97BFF",
    "Swift":      "#ffac45",
    "Ruby":       "#701516",
    "Dockerfile": "#384d54",
    "Vue":        "#41b883",
    "SCSS":       "#c6538c",
}

DEFAULT_LANG_COLORS = ["#38bdf8","#818cf8","#2dd4bf","#fbbf24","#4ade80"]


def gh_api(path, token):
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "profile-card-updater",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {path}")
        if e.code == 403:
            print("  Warning: Received HTTP 403 (Forbidden). You might have hit the GitHub API rate limit.")
            print("  To bypass rate limits, generate a Personal Access Token and set it as GITHUB_TOKEN environment variable.")
        return None


def gh_graphql(query, token):
    url = "https://api.github.com/graphql"
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "profile-card-updater",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  GraphQL HTTP {e.code}")
        return None


def get_stats(token):
    print("Fetching user profile...")
    user = gh_api(f"/users/{USERNAME}", token)
    if not user:
        raise RuntimeError("Could not fetch user profile.")

    public_repos = user.get("public_repos", 0)
    followers    = user.get("followers", 0)

    print("Fetching repositories for stars & forks...")
    total_stars = 0
    total_forks = 0
    page = 1
    while True:
        repos = gh_api(f"/users/{USERNAME}/repos?per_page=100&page={page}", token)
        if not repos or not isinstance(repos, list) or len(repos) == 0:
            break
        for r in repos:
            total_stars += r.get("stargazers_count", 0)
            total_forks += r.get("forks_count", 0)
        if len(repos) < 100:
            break
        page += 1

    # Fetching commits
    from datetime import datetime
    year = datetime.utcnow().year
    total_commits = 0

    if token:
        print("Fetching commit count for this year via GraphQL...")
        gql = f"""
        {{
          user(login: "{USERNAME}") {{
            contributionsCollection(from: "{year}-01-01T00:00:00Z") {{
              totalCommitContributions
            }}
          }}
        }}
        """
        gql_result = gh_graphql(gql, token)
        if gql_result and "data" in gql_result and gql_result.get("data") and gql_result["data"].get("user"):
            total_commits = (gql_result["data"]["user"]
                             ["contributionsCollection"]
                             ["totalCommitContributions"])
    else:
        print("No GitHub token. Fetching commit count for this year via REST Search API...")
        search_path = f"/search/commits?q=author:{USERNAME}+committer-date:>={year}-01-01"
        search_res = gh_api(search_path, token)
        if search_res:
            total_commits = search_res.get("total_count", 0)

    # Rank calculation (simple scoring)
    score = (total_commits * 2 + total_stars * 4 + followers * 1 + public_repos * 1)
    if score >= 2000:   rank = "S+"
    elif score >= 1000: rank = "S"
    elif score >= 500:  rank = "A+"
    elif score >= 200:  rank = "A"
    elif score >= 80:   rank = "B"
    else:               rank = "C"

    return {
        "public_repos":  public_repos,
        "followers":     followers,
        "total_stars":   total_stars,
        "total_forks":   total_forks,
        "total_commits": total_commits,
        "rank":          rank,
    }


def get_languages(token):
    print("Fetching language breakdown...")
    lang_bytes = {}
    page = 1
    while True:
        repos = gh_api(f"/users/{USERNAME}/repos?per_page=100&page={page}", token)
        if not repos or not isinstance(repos, list) or len(repos) == 0:
            break
        for repo in repos:
            if repo.get("fork"):
                continue  # skip forks
            name = repo["name"]
            langs = gh_api(f"/repos/{USERNAME}/{name}/languages", token)
            if langs:
                for lang, b in langs.items():
                    lang_bytes[lang] = lang_bytes.get(lang, 0) + b
        if len(repos) < 100:
            break
        page += 1

    if not lang_bytes:
        return []

    total = sum(lang_bytes.values())
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]
    result = []
    for lang, b in sorted_langs:
        pct = round(b / total * 100, 1)
        color = LANG_COLORS.get(lang, "#8892b0")
        result.append({"name": lang, "pct": pct, "color": color, "bytes": b})
    return result


def update_stats_svg(path, stats):
    print(f"Updating {path}...")
    template_path = path.replace(".svg", ".template.svg")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("{{TOTAL_STARS}}",   f"{stats['total_stars']:,}")
    content = content.replace("{{TOTAL_COMMITS}}", f"{stats['total_commits']:,}")
    content = content.replace("{{PUBLIC_REPOS}}",  f"{stats['public_repos']:,}")
    content = content.replace("{{FOLLOWERS}}",     f"{stats['followers']:,}")
    content = content.replace("{{TOTAL_FORKS}}",   f"{stats['total_forks']:,}")
    content = content.replace("{{RANK}}",          stats["rank"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def update_langs_svg(path, langs):
    print(f"Updating {path}...")
    template_path = path.replace(".svg", ".template.svg")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    total_pct = sum(l["pct"] for l in langs)
    # Ensure we have 5 entries (pad if fewer)
    while len(langs) < 5:
        langs.append({"name": "Other", "pct": 0, "color": DEFAULT_LANG_COLORS[len(langs)], "bytes": 0})

    BAR_MAX = 380.0  # full stack bar width
    BAR_CHART_MAX = 268.0  # individual bar width

    # Calculate stacked bar x offsets
    bar_x = 20.0
    for i, lang in enumerate(langs[:5]):
        w = round(lang["pct"] / 100.0 * BAR_MAX, 1)
        lang["stack_w"] = w
        lang["stack_x"] = round(bar_x, 1)
        bar_x += w

    for i, lang in enumerate(langs[:5]):
        n = i + 1
        bar_w = round(lang["pct"] / 100.0 * BAR_CHART_MAX, 1)
        content = content.replace(f"{{{{LANG{n}_NAME}}}}",  lang["name"])
        content = content.replace(f"{{{{LANG{n}_PCT}}}}",   f"{lang['pct']:.1f}")
        content = content.replace(f"{{{{LANG{n}_COLOR}}}}", lang["color"])
        content = content.replace(f"{{{{LANG{n}_BAR}}}}",  str(bar_w))

    # Stacked bar at top
    content = content.replace("{{BAR1_W}}", str(langs[0]["stack_w"]))
    content = content.replace("{{BAR2_X}}", str(langs[1]["stack_x"]))
    content = content.replace("{{BAR2_W}}", str(langs[1]["stack_w"]))
    content = content.replace("{{BAR3_X}}", str(langs[2]["stack_x"]))
    content = content.replace("{{BAR3_W}}", str(langs[2]["stack_w"]))
    content = content.replace("{{BAR4_X}}", str(langs[3]["stack_x"]))
    content = content.replace("{{BAR4_W}}", str(langs[3]["stack_w"]))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def get_rank_label(score_pct):
    """Convert 0-100 score % to rank label."""
    if score_pct >= 95:  return "SSS"
    if score_pct >= 85:  return "SS"
    if score_pct >= 75:  return "S+"
    if score_pct >= 65:  return "S"
    if score_pct >= 55:  return "A+"
    if score_pct >= 40:  return "A"
    if score_pct >= 25:  return "B"
    return "C"


def update_trophies_svg(path, stats, langs):
    print(f"Updating {path}...")
    template_path = path.replace(".svg", ".template.svg")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    def fill(idx, rank, title, desc, bar):
        n = idx
        nonlocal content
        content = content.replace(f"{{{{T{n}_RANK}}}}", rank)
        content = content.replace(f"{{{{T{n}_TITLE}}}}", title)
        content = content.replace(f"{{{{T{n}_DESC}}}}", desc)
        content = content.replace(f"{{{{T{n}_BAR}}}}", str(bar))

    # Trophy 1: AI / Primary Lang
    lang1_name = langs[0]["name"] if langs else "Python"
    fill(1, "SSS", "Top Coder", f"{lang1_name} Wizard", 132)

    # Trophy 2: Stars
    stars = stats["total_stars"]
    star_rank = "SSS" if stars >= 100 else "SS" if stars >= 50 else "S" if stars >= 20 else "A" if stars >= 5 else "B"
    star_bar  = min(132, round(min(stars, 100) / 100 * 132))
    fill(2, star_rank, "Starstruck", f"Stars: {stars}", star_bar)

    # Trophy 3: Commits
    commits = stats["total_commits"]
    com_rank = "SSS" if commits >= 1000 else "SS" if commits >= 500 else "S" if commits >= 200 else "A" if commits >= 50 else "B"
    com_bar  = min(132, round(min(commits, 1000) / 1000 * 132))
    fill(3, com_rank, "Committer", f"Commits: {commits}", com_bar)

    # Trophy 4: Followers
    fol = stats["followers"]
    fol_rank = "SSS" if fol >= 100 else "SS" if fol >= 50 else "S" if fol >= 25 else "A" if fol >= 10 else "B"
    fol_bar  = min(132, round(min(fol, 100) / 100 * 132))
    fill(4, fol_rank, "Influencer", f"Followers: {fol}", fol_bar)

    # Trophy 5: Repos
    repos = stats["public_repos"]
    rep_rank = "SSS" if repos >= 50 else "S" if repos >= 20 else "A" if repos >= 10 else "B"
    rep_bar  = min(132, round(min(repos, 50) / 50 * 132))
    fill(5, rep_rank, "Creator", f"Repos: {repos}", rep_bar)

    # Trophy 6: Overall Rank
    overall = stats["rank"]
    overall_bar = 132 if "S" in overall else 100 if overall == "A+" else 80 if overall == "A" else 60
    fill(6, overall, "Rank", "Overall Score", overall_bar)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()

    token = args.token
    if not token:
        print("No GITHUB_TOKEN found. Running in unauthenticated/public API mode (rate limits may apply).")

    base = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    print(f"Fetching data for: {USERNAME}")
    print("=" * 50)

    stats = get_stats(args.token)
    langs = get_languages(args.token)

    print("\n--- Stats ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n--- Languages ---")
    for l in langs:
        print(f"  {l['name']}: {l['pct']}%  ({l['color']})")

    print("\n--- Updating SVGs ---")
    update_stats_svg(   os.path.join(base, "harsha-stats.svg"),    stats)
    update_langs_svg(   os.path.join(base, "harsha-langs.svg"),    langs)
    update_trophies_svg(os.path.join(base, "harsha-trophies.svg"), stats, langs)

    print("\nDone! All SVGs updated with live data.")


if __name__ == "__main__":
    main()
