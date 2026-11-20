import json
import os
import shutil
import subprocess
import sys
import time
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
PY_VENV = r"C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"

IST = timezone(timedelta(hours=5, minutes=30))

VIRAL_TOPIC = {
    "id": "01_02_27",
    "day": 83,
    "date_str": "01/02/27",
    "category": "science-curiosity",
    "title": "What If You Never Took A Bath? The 7-Day Cartoon Experiment!",
    "thumb_text": "NEVER TAKE A BATH?!",
    "primary_keyword": "what if you never bathed kids science cartoon",
    "supporting_keywords": ["why hygiene matters animation", "kids bath time science story", "funny cartoon germs experiment"],
    "fact_summary": "Your skin sheds billions of microscopic cells and sweats every day; without soap and warm water, harmless micro-bugs multiply into itchy, stinky grease armies!",
    "hook": "On Day 1, you smell like peanut butter! But on Day 7, tiny tickly germ monsters start throwing a wild dance party on your elbows! What really happens?",
    "publish_slot_est": "2027-02-01T15:30:00-05:00",
    "publish_at_utc": "2027-02-01T20:30:00Z",
    "lines": [
        {"text": "What if you decided to NEVER take a bath again?", "caps": "What if you decided to *NEVER | take a bath *AGAIN?!"},
        {"text": "On Day One, you just smell a tiny bit like peanut butter!", "caps": "On Day One, you just smell | a tiny bit like *PEANUT *BUTTER!"},
        {"text": "By Day Three, sticky sweat traps dust from your soccer shoes!", "caps": "By Day Three, *STICKY sweat traps | dust from your *SOCCER *SHOES!"},
        {"text": "Your head begins to itch like ten playful fleas are jumping around!", "caps": "Your head begins to *ITCH | like ten playful *FLEAS | are jumping *AROUND!"},
        {"text": "On Day Seven, microscopic germ monsters throw a wild party on your elbows!", "caps": "On Day Seven, microscopic *GERM | monsters throw a wild *PARTY | on your *ELBOWS!"},
        {"text": "They munch on dead skin cells and build smelly stink forts!", "caps": "They munch on *DEAD skin cells | and build smelly *STINK *FORTS!"},
        {"text": "Soap is your superhero shield! It washes away bad germs in seconds!", "caps": "*SOAP is your superhero *SHIELD! | It washes away bad *GERMS | in *SECONDS!"},
        {"text": "Warm bubbly water makes you fresh, clean, and ready to conquer the world!", "caps": "Warm bubbly water makes you *FRESH, | clean, and ready to *CONQUER | the *WORLD!"},
        {"text": "Stay fresh and subscribe to BabyBeats Rhymo for daily science fun!", "caps": "*STAY FRESH and *SUBSCRIBE | to *BABYBEATS Rhymo | for daily science *FUN!"}
    ]
}


def build_script_json(topic: dict) -> str:
    data = {
        "title": topic["title"],
        "thumb_text": topic["thumb_text"],
        "voice": "am_puck",
        "speed": 1.05,
        "music": "bed",
        "lead": 0.35,
        "gap": 0.25,
        "outro": 0.85,
        "category": topic["category"],
        "primary_keyword": topic["primary_keyword"],
        "supporting_keywords": topic["supporting_keywords"],
        "fact_summary": topic["fact_summary"],
        "hook": topic["hook"],
        "lines": topic["lines"]
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def build_shots_for_story(topic: dict) -> str:
    shot_blocks = []
    lines = topic["lines"]
    scenes = [
        ("story_intro", "room", f"K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: 'happy', t }}); K.pill('{topic['thumb_text']}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("problem", "blank", "fillAll('#FEF2F2'); P.kidCartoon(380, 860, 1.55, { mood: 'lookDown', t }); K.pill('UH OH!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.6 });"),
        ("shock", "room", "K.room(); P.kidCartoon(540, 860, 1.65, { mood: 'gasp', t }); K.pill('STICKY DUST!', 540, 310, 46, C.red, C.white, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.8 });"),
        ("discovery", "blank", "fillAll('#FFFBEB'); P.kidCartoon(380, 860, 1.5, { mood: 'think', t }); P.magnifier(700, 700, 140); K.pill('ITCHY ITCH!', 540, 310, 44, '#B45309', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("action_step", "room", "K.room(); P.kidCartoon(540, 860, 1.55, { mood: 'gasp', t }); K.pill('GERM PARTY?!', 540, 315, 44, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("kindness", "blank", "fillAll('#FEFCE8'); P.kidCartoon(380, 860, 1.55, { mood: 'sad', t }); K.pill('STINK FORTS!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("heart_moment", "room", "K.room(); P.kidCartoon(540, 860, 1.6, { mood: 'happy', t }); K.pill('SOAP SHIELD!', 540, 310, 46, '#15803D', C.white, eob(seg(lt, 0, 0.4)));", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });"),
        ("moral_truth", "blank", "fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('SUPER FRESH!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.35, 'pop');"),
        ("outro", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4))); K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });")
    ]

    for i in range(len(lines)):
        name, bg, code, sfx = scenes[i % len(scenes)]
        if i == len(lines) - 1:
            name, bg, code, sfx = scenes[-1]
        shot_blocks.append(f"""  {{
    const st = cut({i});
    add({{
      id: 'S{i+1:02d}', at: st, cam: [540, 800], note: 'scene {name}',
      draw(lt, d, t) {{
        {code}
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


def main():
    nt = VIRAL_TOPIC
    tid = nt["id"]
    proj_name = f"{tid}_short"
    proj_dir = ROOT / "videos" / proj_name
    print(f"Creating viral project: {proj_name} ({nt['title']})")

    if not proj_dir.exists():
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(NEW_VIDEO_PS1),
            "-Style", "inside-out", "-Name", proj_name, "-Dir", str(ROOT / "videos")
        ]
        subprocess.run(cmd, check=True)

    # Props & scripts
    shutil.copy2(PROPS_TEMPLATE, proj_dir / "src" / "cartoon_props.js")
    (proj_dir / "script.json").write_text(build_script_json(nt), encoding="utf-8")
    (proj_dir / "src" / "shots.js").write_text(build_shots_for_story(nt), encoding="utf-8")

    (proj_dir / "renders").mkdir(exist_ok=True)
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"

    # 1. Update 30day queue
    q = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    topics = q.setdefault("topics", [])
    if not any(t.get("id") == tid for t in topics):
        topics.append(nt)
        QUEUE_PATH.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Build SEO package
    print("-> Building SEO package...")
    subprocess.run([PY_VENV, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)

    # 3. Render thumbnail
    if not thumb_out.exists():
        print("-> Rendering 1280x720 Thumbnail...")
        try:
            subprocess.run(
                ["node", str(MAKE_THUMB_MJS), str(thumb_out), nt["thumb_text"], nt["category"], "BABYBEATS RHYMO"],
                check=True, timeout=60
            )
        except Exception:
            if not thumb_out.exists():
                raise RuntimeError(f"Thumbnail failed for {tid}")
    print(f"-> Thumbnail verified: {thumb_out.name}")

    # 4. Pipeline MP4 render
    print("-> Executing Audio Synthesis & Video Pipeline (Kokoro + Whisper + Chrome + ffmpeg)...")
    pipe_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(RUN_PIPELINE_PS1),
        "-ProjectDir", str(proj_dir),
        "-OutVideo", str(mp4_out),
        "-SheetStep", "2", "-SheetCols", "5"
    ]
    subprocess.run(pipe_cmd, check=True)

    # 5. FFProbe verification
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(mp4_out)],
        capture_output=True, text=True, check=True
    )
    info = json.loads(probe.stdout)
    vstream = next((s for s in info.get("streams", []) if s.get("width")), {})
    meta = {
        "duration_sec": round(float(info["format"]["duration"]), 2),
        "size_bytes": int(info["format"]["size"]),
        "width": vstream["width"],
        "height": vstream["height"]
    }
    print(f"VERIFIED MP4: {mp4_out.name} ({meta['duration_sec']}s, {meta['size_bytes']} bytes)")

    # 6. Upload queue append
    seo = json.loads(seo_out.read_text(encoding="utf-8"))
    upload_entry = {
        "id": proj_name,
        "topic_id": tid,
        "format": "short",
        "scheduled_slot_est": "15:30 EST",
        "title": seo.get("selected_title") or nt["title"],
        "video_path": str(mp4_out),
        "thumb_path": str(thumb_out),
        "seo_path": str(seo_out),
        "made_for_kids": True,
        "category_id": "27",
        "status": "READY_FOR_UPLOAD",
        "youtube_video_id": None,
        "youtube_url": None,
        "scheduled_publish_est": nt["publish_slot_est"],
        "publish_at": nt["publish_at_utc"],
        "video_specs": meta,
        "updated_at_ist": datetime.now(IST).isoformat()
    }
    uq = json.loads(UPLOAD_Q_PATH.read_text(encoding="utf-8"))
    items = uq.setdefault("items", [])
    existing = next((it for it in items if it.get("id") == upload_entry["id"]), None)
    if existing:
        existing.update(upload_entry)
    else:
        items.append(upload_entry)
    UPLOAD_Q_PATH.write_text(json.dumps(uq, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"SUCCESS: Added {proj_name} to upload_queue.json as READY_FOR_UPLOAD!")


if __name__ == "__main__":
    main()
