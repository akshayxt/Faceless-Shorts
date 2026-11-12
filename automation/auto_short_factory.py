import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"G:\Faceless-Shorts")
AUTO = ROOT / "automation"
QUEUE_PATH = AUTO / "data" / "30day_topic_queue.json"
UPLOAD_Q_PATH = AUTO / "data" / "upload_queue.json"
PROPS_TEMPLATE = AUTO / "templates" / "cartoon_props.js"
NEW_VIDEO_PS1 = ROOT / "skills" / "faceless-shorts" / "scripts" / "new_video.ps1"
RUN_PIPELINE_PS1 = AUTO / "run_pipeline.ps1"
MAKE_THUMB_MJS = AUTO / "make_thumbnail.mjs"
SEO_PY = AUTO / "build_seo_package.py"

IST = timezone(timedelta(hours=5, minutes=30))


def split_fact_sentences(fact_summary: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[.;]+", fact_summary) if len(p.strip()) > 8]
    out = []
    for p in parts[:3]:
        words = p.split()
        if len(words) > 12:
            mid = len(words) // 2
            out.append(" ".join(words[:mid]) + ".")
            out.append(" ".join(words[mid:]) + ".")
        else:
            out.append(p.rstrip(".") + ".")
    while len(out) < 3:
        out.append("Nature uses amazing science tricks right under our noses!")
    return out[:4]


def make_caps_phrase(text: str) -> str:
    clean = re.sub(r"\s+", " ", text.strip())
    words = clean.split()
    chunks = []
    for i in range(0, len(words), 3):
        grp = words[i:i + 3]
        best = max(range(len(grp)), key=lambda k: len(re.sub(r"[^a-zA-Z0-9]", "", grp[k])))
        grp[best] = "*" + grp[best].upper()
        chunks.append(" ".join(grp))
    return " | ".join(chunks)


def build_lines_for_topic(topic: dict) -> list[dict]:
    facts = split_fact_sentences(topic.get("fact_summary", ""))
    kw = re.sub(r"\b(for kids|kids science|cartoon|facts|myth|kids)\b", "", topic["primary_keyword"], flags=re.I)
    kw = re.sub(r"\s+", " ", kw).strip() or "this everyday mystery"
    hook_core = topic["title"].split("|")[0].strip().rstrip("!?.,")
    raw_lines = [
        f"Wait! {hook_core}!",
        f"Most kids guess totally wrong about {kw}!",
        "Stop and picture what actually happens inside.",
        facts[0],
        facts[1],
        facts[2] if len(facts) > 2 else "Look closer—this tiny science detail changes everything!",
        "Even many grown-ups still believe the old rumor instead of this fact!",
        f"Now you know the real truth behind {topic['thumb_text'].title().rstrip('!?')}!",
        "Share this trick with a friend and subscribe to BabyBeats Rhymo!"
    ]
    return [{"text": ln, "caps": make_caps_phrase(ln)} for ln in raw_lines]


def build_shots_js(topic: dict, num_lines: int) -> str:
    cat = topic.get("category", "body-science")
    thumb_badge = topic.get("thumb_text", "FUN FACT!").replace("'", "")
    # Clean, safe, energetic parameterized 7-shot cartoon sequence
    scenes = {
        "body-science": ["xray", "skin", "guards", "kid", "shock", "heart", "outro"],
        "animal-vs": ["creature", "quiz", "creature2", "xray", "spark", "burst", "outro"],
        "myth-bust": ["kid", "mythx", "stomach", "xray", "reveal", "kidhappy", "outro"],
        "space-nature": ["planet", "ray", "planet2", "xray", "reveal", "stars", "outro"],
        "moral-story": ["kid", "batterylow", "spark", "kidhappy", "batteryhigh", "heart", "outro"],
    }
    seq = scenes.get(cat, scenes["body-science"])
    lines_js = []
    for i in range(num_lines):
        sc = seq[i % len(seq)]
        if i == num_lines - 1:
            sc = "outro"
        lines_js.append((i, sc))

    shot_blocks = []
    for i, sc in lines_js:
        if sc == "kid":
            body = f"""
        K.room();
        P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: lt > 1.0 ? 'shock' : 'happy', t }});
        K.pill('{thumb_badge}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6)));
        K.shockLines(540, 740, 260, clamp((lt - 0.8) * 3));"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.5, 'boing', { gain: 0.7 });"
        elif sc == "xray":
            body = """
        K.xray(t);
        K.pill('INSIDE LOOK!', 540, 305, 42, C.yellow, C.ink, eob(seg(lt, 0, 0.3)));
        P.magnifier(540, 740, 230);
        K.heart(540, 740, 2.2, Math.abs(Math.sin(lt * 5)));"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.4, 'heartbeat');"
        elif sc == "skin":
            body = """
        fillAll('#FFFBEB');
        P.skinScene(870, eob(seg(lt, 0.2, 1.0)), 0.4);
        P.kidCartoon(340, 620, 1.25, { mood: 'shock', t });
        K.pill('SCIENCE CHECK!', 540, 310, 42, C.ink, C.yellow, 1);"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.3, 'pop', { gain: 0.7 });"
        elif sc == "guards":
            body = """
        K.xray(t);
        K.pill('BODY TEAM ACTION!', 540, 305, 40, C.yellow, C.ink, 1);
        P.guardCell(330, 760, 1.75, 1, t);
        P.guardCell(750, 760, 1.75, 1, t + 1);
        K.warning(540, 470, eob(seg(lt, 0.2, 0.6)));"""
            sfx = "cue(st, 'alarm', { dur: 1.4 });"
        elif sc == "mythx":
            body = f"""
        fillAll('#FEF2F2');
        P.kidCartoon(360, 860, 1.45, {{ mood: 'shock', t }});
        K.redX(740, 660, 0.9 * eob(seg(lt, 0.2, 0.6)));
        K.pill('MYTH BUSTED!', 540, 310, 44, C.red, C.white, eob(seg(lt, 0.3, 0.6)));"""
            sfx = "cue(st, 'boing', { gain: 0.7 });"
        elif sc == "stomach":
            body = """
        K.xray(t);
        K.insideStomach(t, 1);
        K.pill('BELLY LAB!', 540, 310, 44, C.yellow, C.ink, 1);"""
            sfx = "cue(st, 'bubbles', { dur: 1.5 });"
        elif sc in ("creature", "creature2"):
            col = "'#F97316'" if sc == "creature" else "'#8B5CF6'"
            body = f"""
        fillAll('#ECFDF5');
        K.pill('NATURE SUPERPOWER!', 540, 305, 40, C.ink, C.yellow, 1);
        P.creatureBuddy(540, 760, 1.75 * eob(seg(lt, 0, 0.35)), t, {col});
        K.burst(540, 760, 1.1, 0.5);"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.4, 'pop', { gain: 0.7 });"
        elif sc in ("planet", "planet2", "stars"):
            ring = "true" if sc == "planet2" else "false"
            body = f"""
        fillAll('#0F172A');
        K.pill('SPACE & SKY WONDER!', 540, 305, 40, C.yellow, C.ink, 1);
        P.planetGlobe(540, 750, 200 * eob(seg(lt, 0, 0.4)), t, {ring});"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.5, 'sparkle', { dur: 1.1 });"
        elif sc in ("batterylow", "batteryhigh"):
            pct = "0.18" if sc == "batterylow" else "1.0"
            lbl = "'POWER LOW!'" if sc == "batterylow" else "'100% RECHARGED!'"
            body = f"""
        K.room();
        P.batteryMeter(540, 760, 1.45, {pct});
        K.pill({lbl}, 540, 310, 44, C.ink, C.yellow, 1);"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });"
        elif sc == "outro":
            body = """
        K.room();
        P.kidCartoon(540, 840, 1.65, { mood: 'happy', t });
        K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));
        K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });"
        else:
            body = """
        fillAll('#EFF6FF');
        P.kidCartoon(360, 860, 1.45, { mood: 'happy', t });
        P.magnifier(720, 680, 155);
        K.pill('REAL TRUTH!', 540, 310, 44, '#2A9D8F', C.white, 1);"""
            sfx = "cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.7 });"

        shot_blocks.append(f"""  {{
    const st = cut({i});
    add({{
      id: 'S{i+1:02d}', at: st, cam: [540, 800], note: 'scene {sc}',
      draw(lt, d, t) {{{body}
      }}
    }});
    {sfx}
  }}""")

    return f"""import {{ ctx, C, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, bigText, fillAll, rr, circle, ell, line }} from './core/lib.js';
import {{ L, Le, Wd, T }} from './core/timing.js';
import * as K from './core/kit.js';
import * as P from './cartoon_props.js';

export function buildShots() {{
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {{}}) => CUES.push({{ t: +t.toFixed(3), type, ...o }});
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

{chr(10).join(shot_blocks)}

  return {{ shots: S, cues: CUES }};
}}
"""


def append_upload_queue(entry: dict):
    if UPLOAD_Q_PATH.exists():
        data = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    else:
        data = {"channel_id": "UCR-Di4-tEAdUM7oPzlGn-vg", "items": []}
    items = data.setdefault("items", [])
    existing = next((it for it in items if it.get("id") == entry["id"]), None)
    if existing:
        existing.update(entry)
    else:
        items.append(entry)
    UPLOAD_Q_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    from telegram_logger import wrap_if_top_level
    wrap_if_top_level("SHORT_FACTORY", __file__, sys.argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic-id", help="Specific topic id (e.g. day02). Default: next pending topic")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()

    q = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    topics = q["topics"]
    topic = None
    if args.topic_id:
        topic = next((t for t in topics if t["id"] == args.topic_id), None)
    else:
        topic = next((t for t in topics if t.get("status", "pending") == "pending"), None)

    if not topic:
        print("NO_PENDING_TOPICS")
        return 0

    tid = topic["id"]
    proj_dir = ROOT / "videos" / f"{tid}_short"
    if not proj_dir.exists():
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(NEW_VIDEO_PS1),
            "-Style", "inside-out", "-Name", f"{tid}_short", "-Dir", str(ROOT / "videos")
        ]
        subprocess.run(cmd, check=True)

    shutil.copyfile(PROPS_TEMPLATE, proj_dir / "src" / "cartoon_props.js")
    lines = build_lines_for_topic(topic)
    script = {
        "title": topic["title"],
        "thumb_text": topic.get("thumb_text", "FUN FACT!"),
        "voice": "am_puck",
        "speed": 1.05,
        "music": "bed",
        "lead": 0.35,
        "gap": 0.25,
        "outro": 0.85,
        "sources": topic.get("sources", []),
        "lines": lines
    }
    (proj_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    (proj_dir / "src" / "shots.js").write_text(build_shots_js(topic, len(lines)), encoding="utf-8")

    # Build SEO + 1280x720 Thumbnail
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"
    (proj_dir / "renders").mkdir(exist_ok=True)

    subprocess.run([sys.executable, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)
    subprocess.run(["node", str(MAKE_THUMB_MJS), str(thumb_out), topic.get("thumb_text", "FUN FACT!"), topic.get("category", "body-science"), "BABYBEATS RHYMO"], check=True)

    pipe_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(RUN_PIPELINE_PS1),
        "-ProjectDir", str(proj_dir),
        "-OutVideo", str(mp4_out),
        "-SheetStep", "2", "-SheetCols", "5"
    ]
    if args.skip_render:
        pipe_cmd.append("-SkipRender")
    subprocess.run(pipe_cmd, check=True)

    # Verify rendered MP4 via ffprobe
    meta = {}
    if not args.skip_render:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(mp4_out)],
            capture_output=True, text=True, check=True
        )
        info = json.loads(probe.stdout)
        vstream = next((s for s in info.get("streams", []) if s.get("width")), {})
        if int(vstream.get("width", 0)) != 1080 or int(vstream.get("height", 0)) != 1920:
            raise RuntimeError(f"Unexpected dimensions for {mp4_out}: {vstream}")
        meta = {
            "duration_sec": round(float(info["format"]["duration"]), 2),
            "size_bytes": int(info["format"]["size"]),
            "width": vstream["width"],
            "height": vstream["height"]
        }
        print(f"FFPROBE_VERIFIED {tid}_short: {json.dumps(meta)}", flush=True)

        topic["status"] = "ready_for_upload"
        topic["rendered_at_ist"] = datetime.now(IST).isoformat()
        topic["video_path"] = str(mp4_out)
        topic["thumb_path"] = str(thumb_out)
        topic["seo_path"] = str(seo_out)
        QUEUE_PATH.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")

        seo = json.loads(seo_out.read_text(encoding="utf-8"))
        append_upload_queue({
            "id": f"{tid}_short",
            "topic_id": tid,
            "format": "short",
            "scheduled_slot_est": "15:30 EST",
            "title": seo["selected_title"],
            "video_path": str(mp4_out),
            "thumb_path": str(thumb_out),
            "seo_path": str(seo_out),
            "made_for_kids": True,
            "category_id": "27",
            "status": "READY_FOR_UPLOAD",
            "youtube_video_id": None,
            "youtube_url": None,
            "video_specs": meta,
            "updated_at_ist": datetime.now(IST).isoformat()
        })
        print(f"FACTORY_OK {tid} -> {mp4_out}")
    else:
        print(f"FACTORY_DRY_CHECK_OK {tid} (skipped MP4 render)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
