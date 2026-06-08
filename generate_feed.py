import os
import json
import re
from datetime import datetime, timezone

import feedparser
import requests

MAX_ITEMS_PER_SOURCE = 10
OUTPUT_FILE = "feed.json"


# ── Helpers ────────────────────────────────────────────────────────────────

def fmt_date(dt) -> str:
    """Return human-readable month + year from a time struct or datetime."""
    if isinstance(dt, datetime):
        return dt.strftime("%b %Y")
    if hasattr(dt, 'tm_year'):
        try:
            d = datetime(*dt[:6], tzinfo=timezone.utc)
            return d.strftime("%b %Y")
        except Exception:
            pass
    return ""


def clean_title(title: str) -> str:
    return title.strip()


# ── YouTube ────────────────────────────────────────────────────────────────

def fetch_youtube(channel_id: str) -> list[dict]:
    if not channel_id:
        print("⚠  YOUTUBE_CHANNEL_ID not set, skipping.")
        return []

    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    items = []

    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        # view count lives in media:statistics — try to grab it
        views = ""
        if hasattr(entry, 'media_statistics'):
            v = entry.media_statistics.get('views', '')
            if v:
                views = f"{int(v):,} views"

        meta = f"youtube · {views}" if views else "youtube"

        items.append({
            "type":  "youtube",
            "title": clean_title(entry.title),
            "date":  fmt_date(entry.published_parsed),
            "meta":  meta,
            "url":   entry.link,
        })

    print(f"✓  YouTube: {len(items)} items")
    return items


# ── Medium ─────────────────────────────────────────────────────────────────

def fetch_medium(username: str) -> list[dict]:
    if not username:
        print("⚠  MEDIUM_USERNAME not set, skipping.")
        return []

    rss_url = f"https://medium.com/feed/@{username}"
    feed = feedparser.parse(rss_url)
    items = []

    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        # Estimate read time from content length
        content = ""
        if entry.get('content'):
            content = entry.content[0].value
        elif entry.get('summary'):
            content = entry.summary

        word_count = len(re.sub(r'<[^>]+>', '', content).split())
        read_min   = max(1, round(word_count / 200))
        meta       = f"medium · {read_min} min read"

        items.append({
            "type":  "medium",
            "title": clean_title(entry.title),
            "date":  fmt_date(entry.published_parsed),
            "meta":  meta,
            "url":   entry.link,
        })

    print(f"✓  Medium: {len(items)} items")
    return items


# ── GitHub Releases ────────────────────────────────────────────────────────

def fetch_github_releases(username: str) -> list[dict]:
    if not username:
        print("⚠  GITHUB_USERNAME not set, skipping.")
        return []

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30"
    headers = {"Accept": "application/vnd.github+json"}
    repos = []

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        repos = resp.json() if resp.ok else []
    except Exception as e:
        print(f"⚠  GitHub repos error: {e}")
        return []

    items = []
    for repo in repos:
        if repo.get('fork') or repo.get('private'):
            continue
        rel_url = f"https://api.github.com/repos/{username}/{repo['name']}/releases/latest"
        try:
            rel = requests.get(rel_url, headers=headers, timeout=10).json()
            if rel.get('tag_name'):
                pub = rel.get('published_at', '')
                d   = datetime.fromisoformat(pub.rstrip('Z')).strftime("%b %Y") if pub else ""
                items.append({
                    "type":  "research",
                    "title": rel.get('name') or f"{repo['name']} {rel['tag_name']}",
                    "date":  d,
                    "meta":  f"research · github release · {rel['tag_name']}",
                    "url":   rel.get('html_url', repo['html_url']),
                })
        except Exception:
            pass

        if len(items) >= MAX_ITEMS_PER_SOURCE:
            break

    print(f"✓  GitHub releases: {len(items)} items")
    return items


# ── X / Twitter (manual pinned threads) ───────────────────────────────────
# The free X API doesn't support reading tweets, so we maintain a curated
# list of thread URLs in the X_PINNED_THREADS secret (one URL per line).
# Each URL is stored as-is; titles are derived from the URL slug if possible.

def fetch_x_threads(raw: str) -> list[dict]:
    if not raw:
        print("⚠  X_PINNED_THREADS not set, skipping.")
        return []

    items = []
    for line in raw.strip().splitlines():
        url = line.strip()
        if not url:
            continue
        # Try to derive a human-readable stub from the status ID
        meta = "x · @zgiancana"
        items.append({
            "type":  "x",
            "title": url,       # Replace with real title in the secret: "title|url"
            "date":  "",
            "meta":  meta,
            "url":   url,
        })

    # Support "title|url" format for richer entries
    refined = []
    for item in items:
        if "|" in item["title"]:
            parts = item["title"].split("|", 1)
            # Optional: "title|url|Mon YYYY"
            if len(parts) == 2:
                title, url = parts
                item["title"] = title.strip()
                item["url"]   = url.strip()
            elif len(parts) == 3:
                title, url, date = parts
                item["title"] = title.strip()
                item["url"]   = url.strip()
                item["date"]  = date.strip()
        refined.append(item)

    print(f"✓  X threads: {len(refined)} items")
    return refined

# ── Merge + sort ───────────────────────────────────────────────────────────

def sort_key(item: dict) -> str:
    """Sort by date string descending. Undated items go last."""
    d = item.get("date", "")
    if not d:
        return "0000-00"
    try:
        return datetime.strptime(d, "%b %Y").strftime("%Y-%m")
    except Exception:
        return d


def merge_and_sort(sources: list[list[dict]]) -> list[dict]:
    flat = []
    for source in sources:
        flat.extend(source)
    flat.sort(key=sort_key, reverse=True)
    return flat


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    yt_id      = os.environ.get("YOUTUBE_CHANNEL_ID", "")
    medium_usr = os.environ.get("MEDIUM_USERNAME", "")
    gh_usr     = os.environ.get("GITHUB_USERNAME", "")
    x_threads  = os.environ.get("X_PINNED_THREADS", "")

    items = merge_and_sort([
        fetch_youtube(yt_id),
        fetch_medium(medium_usr),
        fetch_github_releases(gh_usr),
        fetch_x_threads(x_threads),
    ])

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items":      items,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✓  feed.json written — {len(items)} total items")


if __name__ == "__main__":
    main()