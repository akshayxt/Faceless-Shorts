"""
Real-Time US Trending YouTube SEO Optimizer for BabyBeats Rhymo.
Fetches live US YouTube Search Autocomplete suggestions + US Google Trends RSS
(filtered strictly for COPPA-safe kids STEM/nature topics) + live US YouTube
competitor benchmarks, then re-scores and refreshes metadata prior to upload.
"""
import argparse
import json
import re
import socket
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

from build_seo_package import BLOCKED_NON_US_TAGS, build_seo, write_seo_txt

# Force IPv4 on Windows for Google endpoints so IPv6 fallback never stalls HTTP calls
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_google_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host in ("suggestqueries.google.com", "trends.google.com") and family in (0, socket.AF_UNSPEC):
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_google_getaddrinfo

AUTO = Path(r"G:\Faceless-Shorts\automation")
TOPIC_Q = AUTO / "data" / "30day_topic_queue.json"
UPLOAD_Q = AUTO / "data" / "upload_queue.json"
TRENDS_SNAPSHOT = AUTO / "data" / "live_us_trends.json"
IST = timezone(timedelta(hours=5, minutes=30))

SAFE_TREND_WORDS = {
    "science", "space", "nasa", "moon", "planet", "jupiter", "mars", "sun", "eclipse",
    "rainbow", "weather", "snow", "cloud", "rain", "ocean", "whale", "octopus", "bee",
    "bat", "penguin", "cat", "dog", "animal", "brain", "sleep", "dream", "tooth",
    "teeth", "eye", "heart", "blood", "kids", "school", "cartoon", "experiment",
}
UNSAFE_TREND_WORDS = {
    "murder", "death", "killed", "shooting", "war", "election", "trump", "biden",
    "injury", "nba", "nfl", "ufc", "bet", "casino", "crime", "ramsey", "arrest",
    "nsfw", "sex", "drug", "alcohol", "gta",
}
CATEGORY_US_SEEDS = {
    "body-science": ["human body facts for kids", "science facts for kids shorts"],
    "space-nature": ["space facts for kids shorts", "nature science for kids"],
    "animals": ["animal facts for kids shorts", "ocean facts for kids"],
    "funny-story": ["educational cartoons for kids", "moral stories for kids english"],
}


def fetch_yt_suggest_us(seed: str, timeout: float = 6.0) -> list[str]:
    """Fetch live US English YouTube Search Autocomplete suggestions."""
    url = (
        "https://suggestqueries.google.com/complete/search?"
        + urllib.parse.urlencode({
            "client": "firefox",
            "ds": "yt",
            "hl": "en",
            "gl": "US",
            "q": seed,
        })
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [str(x).strip() for x in data[1] if isinstance(x, str) and x.strip()]
    except Exception:
        return []
    return []


def fetch_google_trends_us(timeout: float = 8.0) -> dict:
    """Fetch live US daily trends RSS and keep only child-safe STEM/nature overlaps."""
    url = "https://trends.google.com/trending/rss?geo=US"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw_titles: list[str] = []
    safe_matches: list[str] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rss = resp.read().decode("utf-8", errors="ignore")
        root = ET.fromstring(rss)
        for el in root.findall(".//item/title")[:25]:
            if el.text:
                t = el.text.strip()
                raw_titles.append(t)
                low = t.lower()
                tokens = set(re.findall(r"[a-z]+", low))
                if (tokens & SAFE_TREND_WORDS) and not (tokens & UNSAFE_TREND_WORDS):
                    safe_matches.append(t)
    except Exception:
        pass
    return {
        "fetched_at_ist": datetime.now(IST).isoformat(),
        "raw_us_trend_count": len(raw_titles),
        "safe_kids_trends": safe_matches,
    }


def load_us_benchmark_hashtags() -> list[str]:
    if not TRENDS_SNAPSHOT.exists():
        return []
    try:
        snap = json.loads(TRENDS_SNAPSHOT.read_text(encoding="utf-8"))
        out = []
        for h in snap.get("top_observed_hashtags", []):
            hl = str(h).lower()
            if not any(b in hl for b in BLOCKED_NON_US_TAGS):
                out.append(h)
        return out
    except Exception:
        return []


def derive_query_seeds(topic: dict, is_longform: bool) -> list[str]:
    kw = (
        topic.get("longform_primary_keyword")
        if (is_longform and topic.get("longform_primary_keyword"))
        else topic.get("primary_keyword", "")
    )
    supp = (
        topic.get("longform_supporting_keywords")
        if (is_longform and topic.get("longform_supporting_keywords"))
        else topic.get("supporting_keywords", [])
    )
    core_no_kids = re.sub(r"\b(for kids|cartoon|explained|kids)\b", "", kw, flags=re.I).strip()
    seeds = [
        kw,
        core_no_kids,
        f"{core_no_kids} for kids" if core_no_kids else "",
        *(supp[:2] if isinstance(supp, list) else []),
        *CATEGORY_US_SEEDS.get(topic.get("category", ""), ["science facts for kids"]),
    ]
    dedup = []
    seen = set()
    for s in seeds:
        s_clean = " ".join(str(s).split())
        if s_clean and s_clean.lower() not in seen:
            seen.add(s_clean.lower())
            dedup.append(s_clean)
    return dedup[:5]


def refresh_item(
    item: dict,
    topic: dict,
    trends_info: dict,
    benchmark_hashtags: list[str],
    suggest_cache: dict[str, list[str]],
) -> dict:
    is_longform = item.get("format") == "long"
    seeds = derive_query_seeds(topic, is_longform)
    live_queries: list[str] = []
    seen_q = set()
    for s in seeds:
        if s not in suggest_cache:
            suggest_cache[s] = fetch_yt_suggest_us(s)
        for q in suggest_cache[s]:
            ql = q.lower()
            if ql not in seen_q and not any(b in ql for b in BLOCKED_NON_US_TAGS):
                seen_q.add(ql)
                live_queries.append(q)

    # Match safe US trends relevant to this topic specifically, else empty list
    topic_words = set(re.findall(r"[a-z]+", (topic.get("title", "") + " " + topic.get("primary_keyword", "")).lower()))
    matched_trends = [
        tr for tr in trends_info.get("safe_kids_trends", [])
        if set(re.findall(r"[a-z]+", tr.lower())) & topic_words
    ]

    seo_path = Path(item["seo_path"])
    ch_path = seo_path.parent / "data" / "chapters.json"
    chapters = None
    if is_longform and ch_path.exists():
        chapters = json.loads(ch_path.read_text(encoding="utf-8"))

    seo = build_seo(
        topic,
        is_longform=is_longform,
        chapters=chapters,
        live_queries=live_queries[:10],
        safe_us_trends=matched_trends,
        benchmark_hashtags=benchmark_hashtags,
        fetched_at_ist=trends_info.get("fetched_at_ist"),
    )
    seo_path.write_text(json.dumps(seo, indent=2, ensure_ascii=False), encoding="utf-8")
    vid_p = Path(item["video_path"]) if item.get("video_path") else None
    sched_est = item.get("scheduled_publish_est", item.get("scheduled_slot_est", ""))
    seo_txt_path = write_seo_txt(
        seo,
        seo_path.parent,
        item_id=item["id"],
        video_path=vid_p,
        scheduled_est=sched_est,
    )

    old_title = item.get("title", "")
    item["title"] = seo["selected_title"]
    item["seo_txt_path"] = str(seo_txt_path)
    item["seo_updated_at_ist"] = datetime.now(IST).isoformat()
    item["realtime_seo_score"] = seo["selected_title_lint"].get("score", 0)
    item["realtime_seo_queries"] = seo.get("target_search_queries", [])[:4]
    return {
        "id": item["id"],
        "changed_title": old_title != item["title"],
        "old_title": old_title,
        "new_title": item["title"],
        "score": item["realtime_seo_score"],
        "live_queries_found": len(live_queries),
        "matched_trends": matched_trends,
    }


def refresh_queue(target_id: str | None = None, force: bool = False) -> list[dict]:
    tq = json.loads(TOPIC_Q.read_text(encoding="utf-8"))
    uq = json.loads(UPLOAD_Q.read_text(encoding="utf-8"))
    topics_by_id = {t["id"]: t for t in tq.get("topics", [])}
    trends_info = fetch_google_trends_us()
    benchmark_hashtags = load_us_benchmark_hashtags()
    suggest_cache: dict[str, list[str]] = {}
    results: list[dict] = []

    print(
        f"REALTIME_SEO_SYNC_START us_trends_checked={trends_info['raw_us_trend_count']} "
        f"safe_kids_matches={len(trends_info['safe_kids_trends'])} target={target_id or 'ALL_PENDING'}",
        flush=True,
    )

    for item in uq.get("items", []):
        if target_id and item.get("id") != target_id:
            continue
        if not force and (item.get("status") in ("UPLOADED", "SCHEDULED") or item.get("youtube_video_id")):
            continue
        topic = topics_by_id.get(item.get("topic_id", ""))
        if not topic:
            continue
        res = refresh_item(item, topic, trends_info, benchmark_hashtags, suggest_cache)
        results.append(res)
        marker = "UPDATED" if res["changed_title"] else "VERIFIED"
        print(
            f"SEO_{marker} {res['id']} score={res['score']}/100 yt_suggest={res['live_queries_found']} "
            f"title=\"{res['new_title']}\"",
            flush=True,
        )

    uq["realtime_seo_last_sync_ist"] = datetime.now(IST).isoformat()
    uq["realtime_seo_us_trends_checked"] = trends_info["raw_us_trend_count"]
    UPLOAD_Q.write_text(json.dumps(uq, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"REALTIME_SEO_DONE refreshed={len(results)} items", flush=True)
    return results


def main():
    from telegram_logger import wrap_if_top_level
    wrap_if_top_level("REALTIME_SEO", __file__, sys.argv[1:])

    ap = argparse.ArgumentParser()
    ap.add_argument("--id", help="Refresh real-time SEO for one upload_queue id")
    ap.add_argument("--all", action="store_true", help="Refresh real-time SEO for all un-uploaded queue items")
    ap.add_argument("--force", action="store_true", help="Include UPLOADED/SCHEDULED items too")
    args = ap.parse_args()
    refresh_queue(target_id=args.id if not args.all else None, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
