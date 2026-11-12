import argparse
import importlib.util
import json
import sys
from pathlib import Path

TITLE_PY = Path(r"G:\Faceless-Shorts\skills\yt-package\title.py")
HOOK_PY = Path(r"G:\Faceless-Shorts\skills\yt-script\hookscore.py")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_TITLE_MOD = _load_module("yt_title_linter", TITLE_PY)
_HOOK_MOD = _load_module("yt_hook_scorer", HOOK_PY)


def run_title_check(title: str, thumb: str) -> dict:
    return _TITLE_MOD.check(title, thumb)


def run_hook_check(hook: str) -> dict:
    parts, verdict, name, hits = _HOOK_MOD.score(hook)
    return {
        "hook": hook.strip(),
        "properties": parts,
        "verdict": verdict,
        "band": _HOOK_MOD.band(verdict),
        "formula": name,
        "matched": hits,
    }


BLOCKED_NON_US_TAGS = {
    "hindi", "hinglish", "urdu", "telugu", "tamil", "jee", "neet", "cbse", "upsc",
    "zack d films", "junytony", "aumsum", "binocs", "peekaboo", "cocomelon",
    "blippi", "ms rachel", "ted ed", "scishow", "kurzgesagt", "infobells", "chuchu",
}


def clean_phrase(s: str) -> str:
    s = " ".join(s.strip().split())
    if s.count("(") > s.count(")"):
        s = s.rsplit("(", 1)[0].strip()
    return s.rstrip(" ,:-/|")


def is_complete_title(s: str) -> bool:
    if not s or len(s) > 60:
        return False
    if s.count("(") != s.count(")"):
        return False
    last = s.rstrip(" !?.").split()[-1].lower() if s.split() else ""
    if last in {"a", "an", "the", "in", "on", "to", "of", "for", "and", "or", "with", "at", "by", "inside"}:
        return False
    return True


STOP_SUBJ = {
    "why", "how", "what", "does", "when", "can", "are", "the", "your", "you", "for",
    "kids", "science", "cartoon", "facts", "explained", "story", "really", "actually",
}


def smart_title_case(s: str) -> str:
    minor = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"}
    words = s.split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        if w.isupper() and len(w) > 1:
            out.append(w)
        elif i == 0 or low not in minor:
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(low)
    return " ".join(out)


def topic_tokens(s: str) -> set[str]:
    return {w for w in "".join(c if c.isalnum() else " " for c in s.lower()).split() if len(w) >= 3 and w not in STOP_SUBJ}


def build_title_candidates(topic: dict, base_title: str, thumb: str, live_queries: list[str] | None = None) -> list[str]:
    short_core = clean_phrase(base_title.split("|")[0])
    core_tokens = topic_tokens(short_core)
    thumb_words = {w.lower() for w in thumb.replace("!", "").replace("?", "").split() if len(w) > 2}

    raw = [
        clean_phrase(base_title),
        short_core,
        f"{short_core} #Shorts" if topic.get("format") != "long" else short_core,
    ]
    # Only promote live US YouTube autocomplete queries into title candidates when they match the actual subject (>= 2 core tokens)
    # and skip generic Q&A rewrites for character/story episodes
    if topic.get("category") != "funny-story":
        for q in (live_queries or []):
            q_clean = clean_phrase(q)
            if not (16 <= len(q_clean) <= 50) or any(b in q_clean.lower() for b in BLOCKED_NON_US_TAGS):
                continue
            q_tokens = topic_tokens(q_clean)
            if len(core_tokens & q_tokens) < min(2, len(core_tokens)):
                continue
            titled = smart_title_case(q_clean)
            if "?" not in titled and not titled.endswith("!"):
                is_question = bool(
                    titled.lower().startswith(("why ", "what ", "does ", "do ", "can ", "are ", "is "))
                    or titled.lower().startswith(("how do ", "how does ", "how can ", "how did "))
                )
                titled = titled + ("?" if is_question else "!")
            raw.append(titled)
            if topic.get("format") != "long" and len(titled) <= 52:
                raw.append(f"{titled} #Shorts")

    dedup = []
    seen = set()
    for cand in raw:
        key = cand.lower()
        if key in seen or not is_complete_title(cand):
            continue
        cand_words = {w.lower().strip("!?.,:#()") for w in cand.split() if len(w) > 2}
        if cand != clean_phrase(base_title) and cand != short_core and thumb_words and len(cand_words & thumb_words) > 1:
            continue
        seen.add(key)
        dedup.append(cand)
    return dedup or [clean_phrase(short_core)[:60]]


def filter_us_tags(candidates: list[str], limit: int = 15, max_total_chars: int = 430) -> list[str]:
    out = []
    seen = set()
    total_chars = 0
    for item in candidates:
        tag = clean_phrase(item).lstrip("#")
        low = tag.lower()
        if not tag or len(tag) < 2 or len(tag) > 45 or low in seen:
            continue
        if any(b in low for b in BLOCKED_NON_US_TAGS):
            continue
        if any(ord(c) > 127 for c in tag):
            continue
        if total_chars + len(tag) + 1 > max_total_chars:
            continue
        seen.add(low)
        out.append(tag)
        total_chars += len(tag) + 1
        if len(out) >= limit:
            break
    return out


def build_seo(
    topic: dict,
    is_longform: bool = False,
    chapters: list | None = None,
    live_queries: list[str] | None = None,
    safe_us_trends: list[str] | None = None,
    benchmark_hashtags: list[str] | None = None,
    fetched_at_ist: str | None = None,
) -> dict:
    thumb = (topic.get("longform_thumb_text") if (is_longform and topic.get("longform_thumb_text")) else topic.get("thumb_text", "SECRET FACT!"))
    kw = (topic.get("longform_primary_keyword") if (is_longform and topic.get("longform_primary_keyword")) else topic.get("primary_keyword", topic["title"]))
    base_title = topic.get("longform_title") if (is_longform and topic.get("longform_title")) else topic["title"]
    fact_summary = (topic.get("longform_fact_summary") if (is_longform and topic.get("longform_fact_summary")) else topic.get("fact_summary", ""))
    hook_text = (topic.get("longform_hook") if (is_longform and topic.get("longform_hook")) else topic.get("hook", base_title))
    supp = (topic.get("longform_supporting_keywords") if (is_longform and topic.get("longform_supporting_keywords")) else topic.get("supporting_keywords", []))
    sources = (topic.get("longform_sources") if (is_longform and topic.get("longform_sources")) else topic.get("sources", []))

    topic_for_cands = {**topic, "format": "long" if is_longform else "short"}
    candidates = build_title_candidates(topic_for_cands, base_title, thumb, live_queries=live_queries)
    scored = []
    for c in candidates:
        res = run_title_check(c, thumb)
        scored.append({"title": c, "chars": len(c), "score": res.get("score", 0), "issues": res.get("issues", [])})

    scored.sort(key=lambda x: (-x["score"], x["chars"]))
    selected = scored[0]["title"]
    selected_lint = scored[0]
    clean_base = clean_phrase(base_title)
    base_score = run_title_check(clean_base, thumb)
    short_core = clean_phrase(base_title.split("|")[0])
    short_score = run_title_check(short_core, thumb)
    # Keep the crafted topic title intact unless a live query clearly upgrades CTR without losing clarity
    if is_complete_title(short_core) and short_score.get("score", 0) >= base_score.get("score", 0) and short_score.get("score", 0) >= selected_lint["score"] - 8:
        selected = short_core
        selected_lint = {"title": short_core, "chars": len(short_core), **short_score}
    elif is_complete_title(clean_base) and base_score.get("score", 0) >= selected_lint["score"] - 8:
        selected = clean_base
        selected_lint = {"title": clean_base, "chars": len(clean_base), **base_score}

    hook_info = run_hook_check(hook_text)
    live_queries_clean = [q for q in (live_queries or []) if not any(b in q.lower() for b in BLOCKED_NON_US_TAGS)]
    target_queries = list(dict.fromkeys([kw, *live_queries_clean[:3], *supp]))[:4]

    chapter_block = ""
    if is_longform and chapters:
        chapter_block = "\n\nChapters:\n" + "\n".join(f"{c['time']} - {c['label']}" for c in chapters)

    # First two lines carry exact US search query terms naturally above the fold (yt-seo skill)
    snippet_line_1 = f"{selected} — {hook_text}"
    snippet_line_2 = f"Kids science answer for \"{target_queries[0]}\" with fun 2D animation by BabyBeats Rhymo!"

    trend_block = ""
    if live_queries_clean or safe_us_trends:
        phrases = list(dict.fromkeys([*live_queries_clean[:5], *(safe_us_trends or [])[:3]]))
        trend_block = "\n\nPopular Kids Science Searches (US):\n" + "\n".join(f"- {p}" for p in phrases)

    tag_candidates = [
        *live_queries_clean[:6],
        kw,
        *supp,
        *(safe_us_trends or [])[:3],
        "BabyBeats Rhymo",
        "kids science cartoon",
        "science for kids",
        "educational cartoons for kids",
        "fun facts for kids",
        *(["youtube shorts", "shorts"] if not is_longform else ["kids learning"]),
    ]
    tags = filter_us_tags(tag_candidates, limit=15)

    extra_hashtags = []
    for h in (benchmark_hashtags or []):
        hl = h if h.startswith("#") else f"#{h}"
        if any(b in hl.lower() for b in BLOCKED_NON_US_TAGS):
            continue
        if hl.lower() in {"#shorts", "#kidsscience", "#sciencefacts", "#humanbodyfacts", "#oceanfacts", "#spacefacts", "#animalfacts", "#facts", "#kids"}:
            extra_hashtags.append(hl)
    hashtags_raw = [
        "#BabyBeatsRhymo", "#KidsScience", "#ScienceForKids", "#EducationalCartoons",
        *(["#Shorts"] if not is_longform else ["#KidsLearning"]),
        *extra_hashtags
    ]
    hashtags = []
    seen_h = set()
    for h in hashtags_raw:
        if h.lower() not in seen_h:
            seen_h.add(h.lower())
            hashtags.append(h)
        if len(hashtags) >= 6:
            break

    desc = (
        f"{snippet_line_1}\n"
        f"{snippet_line_2}\n\n"
        f"{fact_summary}\n\n"
        f"BabyBeats Rhymo creates kid-safe 2D science cartoons and funny educational stories every day for curious US kids and families!"
        f"{chapter_block}"
        f"{trend_block}\n\n"
        f"Sources & Fact Check:\n" + "\n".join(f"- {u}" for u in sources) + "\n\n"
        + " ".join(hashtags)
    ).strip()

    playlist = "Kids Science & Body Mysteries (Cartoons)" if topic.get("category") in ("body-science", "space-nature") else "Funny Kids Myths & Animal Superpowers"
    pinned_comment = "Did you know this before today? Drop your next curious science question below!"

    return {
        "topic_id": topic["id"],
        "format": "long" if is_longform else "short",
        "title_options": scored,
        "selected_title": selected,
        "selected_title_lint": selected_lint,
        "thumb_text": thumb,
        "hook_lint": hook_info,
        "primary_keyword": kw,
        "supporting_keywords": supp,
        "target_search_queries": target_queries,
        "realtime_seo": {
            "mode": "live_us_autocomplete_and_trends" if live_queries_clean or fetched_at_ist else "local_curated",
            "fetched_at_ist": fetched_at_ist,
            "live_yt_suggest_queries": live_queries_clean[:8],
            "matched_safe_us_trends": safe_us_trends or [],
            "observed_us_hashtags": extra_hashtags,
        },
        "description": desc,
        "tags": tags,
        "hashtags": hashtags,
        "chapters": chapters or [],
        "pinned_comment": pinned_comment,
        "playlist_recommendation": playlist,
        "youtube_settings": {
            "category_id": "27",
            "default_language": "en",
            "default_audio_language": "en-US",
            "made_for_kids": True,
            "privacy_status": "public",
            "contains_synthetic_media": False
        }
    }


def format_seo_txt(seo: dict, item_id: str | None = None, scheduled_est: str | None = None) -> str:
    """Render copy-paste-ready YouTube Studio SEO text formatted for US audiences."""
    rt = seo.get("realtime_seo", {})
    trending = list(dict.fromkeys([
        *rt.get("live_yt_suggest_queries", []),
        *rt.get("matched_safe_us_trends", []),
        *seo.get("target_search_queries", []),
    ]))
    if not trending:
        trending = [seo.get("primary_keyword", ""), *seo.get("supporting_keywords", [])]
    trending_lines = "\n".join(f"- {q}" for q in trending if q)
    hashtags_str = " ".join(seo.get("hashtags", []))
    tags_str = ", ".join(seo.get("tags", []))

    header = f"Video ID : {item_id or seo.get('topic_id', '')}"
    if scheduled_est:
        header += f" | Scheduled Slot (US Eastern) : {scheduled_est}"

    return (
        f"{header}\n"
        f"Target Audience : United States (en-US, Kids & Families, Made For Kids)\n"
        f"SEO Lint Score : {seo.get('selected_title_lint', {}).get('score', '?')}/100 | "
        f"Hook Score : {seo.get('hook_lint', {}).get('verdict', '?')}/100 ({seo.get('hook_lint', {}).get('band', '')})\n"
        f"Category : {seo.get('youtube_settings', {}).get('category_id', '27')} (Education) | "
        f"Thumbnail Text : {seo.get('thumb_text', '')}\n"
        f"{'=' * 72}\n\n"
        f"Title :\n"
        f"{seo.get('selected_title', '')}\n\n"
        f"US Targeted Audience Description (SEO & Video Explanation) :\n"
        f"{seo.get('description', '')}\n\n"
        f"Real-Time Trending Keywords :\n"
        f"{trending_lines}\n\n"
        f"Hashtags :\n"
        f"{hashtags_str}\n\n"
        f"Video Keywords :\n"
        f"{tags_str}\n"
    )


def write_seo_txt(
    seo: dict,
    proj_dir: Path,
    item_id: str | None = None,
    video_path: Path | None = None,
    scheduled_est: str | None = None,
) -> Path:
    """Save formatted SEO .txt inside both project folder and right next to the rendered MP4."""
    txt = format_seo_txt(seo, item_id=item_id, scheduled_est=scheduled_est)
    proj_txt = proj_dir / "seo.txt"
    proj_txt.write_text(txt, encoding="utf-8")
    if video_path:
        renders_txt = video_path.parent / f"{video_path.stem}_seo.txt"
        renders_txt.parent.mkdir(parents=True, exist_ok=True)
        renders_txt.write_text(txt, encoding="utf-8")
        return renders_txt
    return proj_txt


def main():
    from telegram_logger import wrap_if_top_level
    wrap_if_top_level("SEO_BUILDER", __file__, sys.argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic-id", required=True)
    ap.add_argument("--queue", default=r"G:\Faceless-Shorts\automation\data\30day_topic_queue.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--longform", action="store_true")
    ap.add_argument("--chapters-file")
    args = ap.parse_args()

    q = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    topic = next((t for t in q["topics"] if t["id"] == args.topic_id), None)
    if not topic:
        raise SystemExit(f"Topic not found: {args.topic_id}")
    chapters = None
    ch_path = Path(args.chapters_file) if args.chapters_file else (Path(args.out).parent / "data" / "chapters.json")
    if args.longform and ch_path.exists():
        chapters = json.loads(ch_path.read_text(encoding="utf-8"))
    seo = build_seo(topic, is_longform=args.longform, chapters=chapters)
    out_p = Path(args.out)
    out_p.write_text(json.dumps(seo, indent=2, ensure_ascii=False), encoding="utf-8")
    fmt_tag = "longform" if args.longform else "short"
    vid_guess = out_p.parent / "renders" / f"{args.topic_id}_{fmt_tag}.mp4"
    txt_p = write_seo_txt(seo, out_p.parent, item_id=f"{args.topic_id}_{fmt_tag}", video_path=vid_guess if vid_guess.parent.exists() else None)
    print(f"SEO package written -> {args.out} & {txt_p} (selected: {seo['selected_title']})")


if __name__ == "__main__":
    main()
