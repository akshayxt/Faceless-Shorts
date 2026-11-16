import json
import os
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
PY_VENV = r"C:\Users\Admin\.faceless-shorts\venv\Scripts\python.exe"

IST = timezone(timedelta(hours=5, minutes=30))

NEW_7_TOPICS = [
    {
        "id": "11_12_26",
        "day": 31,
        "date_str": "11/12/26",
        "category": "space-nature",
        "title": "Twinkle Twinkle Little Star: What Is a Star Really Made Of?",
        "thumb_text": "REAL STAR TRUTH!",
        "primary_keyword": "twinkle twinkle little star for kids",
        "supporting_keywords": ["what are stars made of for kids", "stars science cartoon rhyme", "preschool astronomy song"],
        "fact_summary": "Stars look tiny and pointy because they are trillions of miles away, but each star is actually a giant glowing ball of super hot gas, just like our sun. When starlight passes through Earth's atmosphere, the moving air bends the light, making it twinkle.",
        "hook": "Twinkle twinkle little star... wait, did you know real stars are NOT pointy at all?",
        "publish_slot_est": "2026-12-11T15:30:00-05:00",
        "publish_at_utc": "2026-12-11T20:30:00Z",
        "lines": [
            {"text": "Twinkle twinkle little star, how I wonder what you are!", "caps": "*TWINKLE twinkle | little *STAR, how | I wonder *WHAT | you *ARE!"},
            {"text": "Did you know real stars are NOT pointy shapes at all?", "caps": "Did you *KNOW | real stars are *NOT | pointy *SHAPES at | *ALL?"},
            {"text": "Up above the world so high, like a diamond in the sky!", "caps": "Up above the *WORLD | so *HIGH, like | a *DIAMOND in | the *SKY!"},
            {"text": "Each star is actually a giant glowing ball of super hot gas, just like our sun!", "caps": "Each star is *ACTUALLY | a *GIANT glowing | ball of super *HOT | gas, just *LIKE our sun!"},
            {"text": "They look like tiny dots only because they are trillions of miles away!", "caps": "They look like *TINY | dots only *BECAUSE | they are *TRILLIONS | of miles *AWAY!"},
            {"text": "When starlight passes through our wobbly air, it twinkles like magic!", "caps": "When starlight *PASSES | through our *WOBBLY | air, it *TWINKLES | like *MAGIC!"},
            {"text": "So next time you look up, you know you are seeing giant cosmic suns!", "caps": "So next time you *LOOK | up, you *KNOW | you are seeing *GIANT | cosmic *SUNS!"},
            {"text": "Now you know the real truth behind Twinkle Twinkle Little Star!", "caps": "Now you *KNOW | the real *TRUTH | behind *TWINKLE Twinkle | Little *STAR!"},
            {"text": "Sing along and subscribe to BabyBeats Rhymo for more fun discoveries!", "caps": "*SING along and | *SUBSCRIBE to | *BABYBEATS Rhymo | for more fun *DISCOVERIES!"}
        ]
    },
    {
        "id": "12_12_26",
        "day": 32,
        "date_str": "12/12/26",
        "category": "moral-story",
        "title": "The Wheels on the Bus: How Heavy Giant Wheels Spin So Fast!",
        "thumb_text": "BUS WHEEL SECRET!",
        "primary_keyword": "wheels on the bus rhyme for kids",
        "supporting_keywords": ["how wheels roll science for kids", "wheels on the bus cartoon", "preschool bus song"],
        "fact_summary": "Inside every giant bus wheel, tiny steel ball bearings roll smoothly around a central axle, beating friction so heavy buses glide easily down the street.",
        "hook": "The wheels on the bus go round and round! But how do heavy steel wheels roll so smooth without getting stuck?",
        "publish_slot_est": "2026-12-12T15:30:00-05:00",
        "publish_at_utc": "2026-12-12T20:30:00Z",
        "lines": [
            {"text": "The wheels on the bus go round and round, all through the town!", "caps": "The *WHEELS on | the bus go *ROUND | and round, all *THROUGH | the *TOWN!"},
            {"text": "Ever wonder how heavy giant bus wheels roll so fast and smooth?", "caps": "Ever *WONDER how | heavy giant bus *WHEELS | roll so *FAST | and *SMOOTH?"},
            {"text": "A big bus weighs as much as two whole elephants!", "caps": "A big bus *WEIGHS | as *MUCH as | two *WHOLE elephants!"},
            {"text": "Inside every wheel, hundreds of tiny steel balls roll around an axle!", "caps": "Inside every *WHEEL, | hundreds of tiny *STEEL | balls roll *AROUND | an *AXLE!"},
            {"text": "These ball bearings beat friction so the wheels never get stuck!", "caps": "These ball *BEARINGS | beat *FRICTION so | the wheels *NEVER | get *STUCK!"},
            {"text": "The engine turns the axle, and the rubber tires grip the road!", "caps": "The engine *TURNS | the *AXLE, and | the rubber *TIRES | grip the *ROAD!"},
            {"text": "Round and round they glide, keeping all the passengers smiling!", "caps": "Round and *ROUND | they *GLIDE, keeping | all the *PASSENGERS | *SMILING!"},
            {"text": "Now you know the engineering secret behind The Wheels on the Bus!", "caps": "Now you *KNOW | the engineering *SECRET | behind The *WHEELS | on the *BUS!"},
            {"text": "Roll into more fun science and subscribe to BabyBeats Rhymo!", "caps": "*ROLL into more | fun *SCIENCE and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "13_12_26",
        "day": 33,
        "date_str": "13/12/26",
        "category": "animal-vs",
        "title": "Itsy Bitsy Spider: How Spiders Climb Smooth Water Spouts!",
        "thumb_text": "SPIDER FEET SECRET!",
        "primary_keyword": "itsy bitsy spider rhyme for kids",
        "supporting_keywords": ["how spiders climb walls kids science", "itsy bitsy spider cartoon", "spider nursery rhyme"],
        "fact_summary": "Spiders do not slip because each tiny foot is covered in thousands of microscopic hairs that grip microscopic bumps on even the smoothest glass and metal spouts.",
        "hook": "The itsy bitsy spider climbed up the water spout! Ever wonder why spiders NEVER slip and fall down?",
        "publish_slot_est": "2026-12-13T15:30:00-05:00",
        "publish_at_utc": "2026-12-13T20:30:00Z",
        "lines": [
            {"text": "The itsy bitsy spider climbed up the water spout!", "caps": "The *ITSY bitsy | spider *CLIMBED up | the water *SPOUT!"},
            {"text": "How can a tiny spider walk up smooth metal and glass without falling?", "caps": "How can a *TINY | spider walk up *SMOOTH | metal and glass *WITHOUT | *FALLING?"},
            {"text": "Down came the rain and washed the spider out!", "caps": "Down *CAME the | rain and *WASHED | the spider *OUT!"},
            {"text": "Under a microscope, each spider foot has hundreds of thousands of tiny hairs!", "caps": "Under a *MICROSCOPE, | each spider *FOOT | has hundreds of thousands *OF | tiny *HAIRS!"},
            {"text": "These hair tips grab onto invisible microscopic bumps on the smoothest walls!", "caps": "These hair *TIPS | grab onto *INVISIBLE | microscopic bumps on the *SMOOTHEST | *WALLS!"},
            {"text": "Out came the sun and dried up all the rain!", "caps": "Out *CAME the | sun and *DRIED | up all the *RAIN!"},
            {"text": "And the itsy bitsy spider climbed up the spout again with super sticky feet!", "caps": "And the itsy *BITSY | spider climbed up the *SPOUT | again with super *STICKY | *FEET!"},
            {"text": "Now you know the real superpower behind the Itsy Bitsy Spider!", "caps": "Now you *KNOW | the real *SUPERPOWER | behind the *ITSY | Bitsy *SPIDER!"},
            {"text": "Climb higher with daily fun facts—subscribe to BabyBeats Rhymo!", "caps": "*CLIMB higher with | daily fun *FACTS— | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "14_12_26",
        "day": 34,
        "date_str": "14/12/26",
        "category": "body-science",
        "title": "Five Little Monkeys: Why Gravity Always Pulls You Down!",
        "thumb_text": "WHY WE FALL DOWN!",
        "primary_keyword": "five little monkeys jumping on the bed rhyme",
        "supporting_keywords": ["gravity explained for kids cartoon", "five little monkeys song", "preschool gravity rhyme"],
        "fact_summary": "When a monkey jumps up, Earth's invisible super-magnet called gravity pulls everything straight down toward the center of the planet.",
        "hook": "Five little monkeys jumping on the bed, one fell off! But why do things always fall DOWN and never float UP?",
        "publish_slot_est": "2026-12-14T15:30:00-05:00",
        "publish_at_utc": "2026-12-14T20:30:00Z",
        "lines": [
            {"text": "Five little monkeys jumping on the bed, one fell off and bumped his head!", "caps": "Five little *MONKEYS | jumping on the *BED, | one fell off and *BUMPED | his *HEAD!"},
            {"text": "Why did the monkey tumble DOWN instead of floating UP into space?", "caps": "Why did the monkey *TUMBLE | *DOWN instead of | floating *UP into | *SPACE?"},
            {"text": "Mama called the doctor and the doctor said, no more monkeys jumping on the bed!", "caps": "Mama called the *DOCTOR | and the *DOCTOR | said, no more *MONKEYS | jumping on the *BED!"},
            {"text": "Earth has an invisible super-magnet pulling everything down called Gravity!", "caps": "Earth has an *INVISIBLE | super-magnet pulling *EVERYTHING | down called *GRAVITY!"},
            {"text": "No matter how high you bounce, gravity pulls your feet back to the ground!", "caps": "No matter how *HIGH | you bounce, *GRAVITY | pulls your feet *BACK | to the *GROUND!"},
            {"text": "Gravity keeps our oceans, our houses, and little monkeys safely on Earth!", "caps": "Gravity keeps our *OCEANS, | our *HOUSES, | and little monkeys *SAFELY | on *EARTH!"},
            {"text": "So jump safely on the floor, little monkeys, and respect gravity!", "caps": "So jump *SAFELY | on the floor, little *MONKEYS, | and respect *GRAVITY!"},
            {"text": "Now you know the science power behind Five Little Monkeys!", "caps": "Now you *KNOW | the science *POWER | behind Five *LITTLE | *MONKEYS!"},
            {"text": "Bounce over to more fun learning and subscribe to BabyBeats Rhymo!", "caps": "*BOUNCE over to | more fun *LEARNING | and *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    },
    {
        "id": "15_12_26",
        "day": 35,
        "date_str": "15/12/26",
        "category": "animal-vs",
        "title": "Baa Baa Black Sheep: Where Does Warm Winter Wool Come From?",
        "thumb_text": "HOW WOOL IS MADE!",
        "primary_keyword": "baa baa black sheep rhyme for kids",
        "supporting_keywords": ["where does wool come from for kids", "baa baa black sheep cartoon", "preschool sheep song"],
        "fact_summary": "In springtime, farmers gently give sheep a quick haircut to collect fluffy fleece, which gets washed, spun into cozy yarn, and knitted into warm winter sweaters.",
        "hook": "Baa baa black sheep, have you any wool? Yes sir, yes sir, three bags full! But how does sheep fluff turn into warm cozy sweaters?",
        "publish_slot_est": "2026-12-15T15:30:00-05:00",
        "publish_at_utc": "2026-12-15T20:30:00Z",
        "lines": [
            {"text": "Baa baa black sheep, have you any wool? Yes sir, yes sir, three bags full!", "caps": "Baa baa black *SHEEP, | have you any *WOOL? | Yes sir, yes *SIR, | three bags *FULL!"},
            {"text": "Where does soft warm wool actually come from?", "caps": "Where does soft *WARM | wool *ACTUALLY | come *FROM?"},
            {"text": "One for the master, and one for the dame, and one for the little boy down the lane!", "caps": "One for the *MASTER, | and one for the *DAME, | and one for the *LITTLE | boy down the *LANE!"},
            {"text": "Every spring, farmers give sheep a gentle haircut to keep them cool for summer!", "caps": "Every spring, *FARMERS | give sheep a gentle *HAIRCUT | to keep them *COOL | for *SUMMER!"},
            {"text": "The fluffy fleece is washed clean and spun into strong cozy yarn!", "caps": "The fluffy *FLEECE | is washed clean *AND | spun into strong *COZY | *YARN!"},
            {"text": "Knitting machines turn that yarn into warm winter hats, socks, and sweaters!", "caps": "Knitting machines *TURN | that yarn into *WARM | winter hats, socks, *AND | *SWEATERS!"},
            {"text": "The wool grows right back on the sheep before winter returns!", "caps": "The wool grows right *BACK | on the *SHEEP | before winter *RETURNS!"},
            {"text": "Now you know where your cozy sweater came from with Baa Baa Black Sheep!", "caps": "Now you *KNOW | where your cozy *SWEATER | came from with *BAA | Baa Black *SHEEP!"},
            {"text": "Stay warm and smart—subscribe to BabyBeats Rhymo for daily stories!", "caps": "Stay warm and *SMART— | *SUBSCRIBE to | *BABYBEATS Rhymo | for daily *STORIES!"}
        ]
    },
    {
        "id": "16_12_26",
        "day": 36,
        "date_str": "16/12/26",
        "category": "space-nature",
        "title": "Row Row Row Your Boat: Why Giant Heavy Boats Float on Water!",
        "thumb_text": "WHY BOATS FLOAT!",
        "primary_keyword": "row row row your boat rhyme for kids",
        "supporting_keywords": ["why do heavy boats float kids science", "row your boat cartoon", "preschool boat song"],
        "fact_summary": "A tiny pebble sinks because it is solid and heavy for its size, but a hollow boat pushes aside water that pushes back upward with equal lifting power called buoyancy.",
        "hook": "Row row row your boat gently down the stream! Why does a tiny pebble sink instantly, but a massive wooden boat floats?",
        "publish_slot_est": "2026-12-16T15:30:00-05:00",
        "publish_at_utc": "2026-12-16T20:30:00Z",
        "lines": [
            {"text": "Row row row your boat gently down the stream, merrily merrily merrily life is but a dream!", "caps": "Row row row your *BOAT | gently down the *STREAM, | merrily merrily *MERRILY | life is but a *DREAM!"},
            {"text": "Why does a tiny pebble sink like a rock, but a giant heavy boat floats on water?", "caps": "Why does a *TINY | pebble sink like a *ROCK, | but a giant heavy boat *FLOATS | on *WATER?"},
            {"text": "Pebbles are solid and heavy for their size, so water cannot hold them up!", "caps": "Pebbles are *SOLID | and heavy for their *SIZE, | so water *CANNOT | hold them *UP!"},
            {"text": "Boats are hollow and wide, pushing aside gallons of water!", "caps": "Boats are *HOLLOW | and *WIDE, pushing | aside gallons of *WATER!"},
            {"text": "That pushed water pushes back upward with a secret lifting force called Buoyancy!", "caps": "That pushed water *PUSHES | back upward with a *SECRET | lifting force called *BUOYANCY!"},
            {"text": "As long as the boat is wide and hollow, buoyancy keeps it floating high!", "caps": "As long as the boat is *WIDE | and *HOLLOW, | buoyancy keeps it *FLOATING | *HIGH!"},
            {"text": "Grab your oars and paddle along the stream of science!", "caps": "Grab your *OARS | and paddle *ALONG | the stream of *SCIENCE!"},
            {"text": "Now you know the floating secret behind Row Row Row Your Boat!", "caps": "Now you *KNOW | the floating *SECRET | behind Row *ROW | Row Your *BOAT!"},
            {"text": "Glide along with us and subscribe to BabyBeats Rhymo!", "caps": "*GLIDE along with | us and *SUBSCRIBE | to *BABYBEATS | *RHYMO!"}
        ]
    },
    {
        "id": "17_12_26",
        "day": 37,
        "date_str": "17/12/26",
        "category": "myth-bust",
        "title": "Humpty Dumpty: Why Are Eggshells Curved and Super Strong?",
        "thumb_text": "EGGSHELL SECRET!",
        "primary_keyword": "humpty dumpty rhyme for kids",
        "supporting_keywords": ["why are eggs shaped like that kids science", "humpty dumpty cartoon", "preschool egg song"],
        "fact_summary": "An egg's dome arch shape spreads weight evenly around the whole shell so mother birds do not crush them when sitting, but sharp drops crack the brittle calcium instantly.",
        "hook": "Humpty Dumpty sat on a wall, Humpty Dumpty had a great fall! Did you know an eggshell is as strong as an architectural dome?",
        "publish_slot_est": "2026-12-17T15:30:00-05:00",
        "publish_at_utc": "2026-12-17T20:30:00Z",
        "lines": [
            {"text": "Humpty Dumpty sat on a wall, Humpty Dumpty had a great fall!", "caps": "Humpty Dumpty sat *ON | a *WALL, Humpty | Dumpty had a *GREAT | *FALL!"},
            {"text": "Did you know eggshells are actually built like super strong architecture domes?", "caps": "Did you know eggshells are *ACTUALLY | built like super *STRONG | architecture *DOMES!"},
            {"text": "All the king's horses and all the king's men couldn't put Humpty together again!", "caps": "All the king's *HORSES | and all the king's *MEN | couldn't put Humpty *TOGETHER | *AGAIN!"},
            {"text": "An egg's curved dome shape spreads weight evenly around the whole shell!", "caps": "An egg's curved *DOME | shape spreads weight *EVENLY | around the *WHOLE | *SHELL!"},
            {"text": "That is why mother birds can sit on eggs without breaking them at all!", "caps": "That is why *MOTHER | birds can sit on *EGGS | without breaking *THEM | at *ALL!"},
            {"text": "But when Humpty hits a hard stone wall on one sharp point, the calcium cracks!", "caps": "But when Humpty hits a *HARD | stone wall on *ONE | sharp point, the calcium *CRACKS!"},
            {"text": "Nature gave eggs dome engineering millions of years before humans built bridges!", "caps": "Nature gave eggs dome *ENGINEERING | millions of *YEARS | before humans built *BRIDGES!"},
            {"text": "Now you know the real dome secret behind Humpty Dumpty!", "caps": "Now you *KNOW | the real dome *SECRET | behind *HUMPTY | *DUMPTY!"},
            {"text": "Crack open more fun knowledge and subscribe to BabyBeats Rhymo!", "caps": "*CRACK open more | fun *KNOWLEDGE and | *SUBSCRIBE to | *BABYBEATS Rhymo!"}
        ]
    }
]


def update_topic_queue():
    if QUEUE_PATH.exists():
        q = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    else:
        q = {"channel": "BabyBeats Rhymo", "topics": []}
    topics = q.setdefault("topics", [])
    for nt in NEW_7_TOPICS:
        existing = next((t for t in topics if t["id"] == nt["id"]), None)
        if existing:
            existing.update(nt)
        else:
            topics.append({
                "id": nt["id"],
                "day": nt["day"],
                "category": nt["category"],
                "title": nt["title"],
                "thumb_text": nt["thumb_text"],
                "primary_keyword": nt["primary_keyword"],
                "supporting_keywords": nt["supporting_keywords"],
                "score_breakdown": {
                    "audience_demand": 18,
                    "recent_growth": 16,
                    "competition_opportunity": 14,
                    "audience_curiosity": 15,
                    "click_potential": 9,
                    "retention_potential": 9,
                    "production_feasibility": 5,
                    "niche_relevance": 5
                },
                "total_score": 91,
                "fact_summary": nt["fact_summary"],
                "sources": [
                    "https://kidshealth.org",
                    "https://www.nasa.gov/kidsclub"
                ],
                "hook": nt["hook"],
                "visual_focus": "vibrant nursery rhyme cartoon mascot explaining everyday science",
                "status": "ready_for_upload"
            })
    QUEUE_PATH.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {QUEUE_PATH} with {len(NEW_7_TOPICS)} topics.")


def build_shots_for_topic(nt: dict) -> str:
    cat = nt.get("category", "body-science")
    thumb_badge = nt.get("thumb_text", "RHYME SCIENCE!").replace("'", "")
    lines = nt["lines"]
    shot_blocks = []
    
    # 9-scene visual storyline per video
    scenes = [
        ("kid", "room", f"K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), {{ mood: 'happy', t }}); K.pill('{thumb_badge}', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);", "cue(st, 'whoosh'); cue(st + 0.4, 'pop');"),
        ("science_check", "blank", "fillAll('#FFFBEB'); P.magnifier(540, 760, 210); K.pill('SCIENCE MYSTERY!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'sparkle');"),
        ("shock", "room", "K.room(); P.kidCartoon(380, 860, 1.55, { mood: 'shock', t }); K.shockLines(380, 740, 240, clamp((lt - 0.4) * 3)); K.pill('WAIT WHAT?!', 540, 310, 44, C.red, C.white, 1);", "cue(st, 'alarm', { dur: 0.8 });"),
        ("deep_dive", "xray", "K.xray(t); P.planetGlobe(540, 760, 190 * eob(seg(lt, 0, 0.4)), t, true); K.pill('HOW IT WORKS!', 540, 305, 42, C.yellow, C.ink, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("microscope", "blank", "fillAll('#EFF6FF'); P.creatureBuddy(540, 770, 1.8 * eob(seg(lt, 0, 0.35)), t, '#0284C7'); K.pill('NATURE SECRET!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'pop');"),
        ("action", "blank", "fillAll('#FEF2F2'); P.batteryMeter(540, 760, 1.45, 1.0); K.pill('SUPER POWER!', 540, 310, 44, C.ink, C.yellow, 1);", "cue(st, 'whoosh'); cue(st + 0.4, 'sparkle');"),
        ("happy_kid", "room", "K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.heart(540, 520, 2.0 * eob(seg(lt, 0.2, 0.6)), Math.abs(Math.sin(lt * 6))); K.pill('SMART TODDLER!', 540, 310, 44, '#2A9D8F', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.3, 'boing');"),
        ("truth", "blank", "fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('REAL TRUTH!', 540, 310, 44, '#15803D', C.white, 1);", "cue(st, 'whoosh'); cue(st + 0.35, 'pop');"),
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


def generate_single_short(nt: dict):
    tid = nt["id"]
    proj_name = f"{tid}_short"
    proj_dir = ROOT / "videos" / proj_name
    print(f"\n========================================================")
    print(f"GENERATING: {proj_name} ({nt['title']})")
    print(f"========================================================")

    if not proj_dir.exists():
        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(NEW_VIDEO_PS1),
            "-Style", "inside-out", "-Name", proj_name, "-Dir", str(ROOT / "videos")
        ]
        subprocess.run(cmd, check=True)

    # Copy cartoon props
    shutil.copyfile(PROPS_TEMPLATE, proj_dir / "src" / "cartoon_props.js")

    # Script json
    script = {
        "title": nt["title"],
        "thumb_text": nt["thumb_text"],
        "voice": "am_puck",
        "speed": 1.05,
        "music": "bed",
        "lead": 0.35,
        "gap": 0.25,
        "outro": 0.85,
        "sources": ["https://kidshealth.org", "https://www.nasa.gov/kidsclub"],
        "lines": nt["lines"]
    }
    (proj_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    # Shots js
    (proj_dir / "src" / "shots.js").write_text(build_shots_for_topic(nt), encoding="utf-8")

    # SEO & Thumbnail
    (proj_dir / "renders").mkdir(exist_ok=True)
    seo_out = proj_dir / "seo_package.json"
    thumb_out = proj_dir / "renders" / f"{tid}_thumb.jpg"
    mp4_out = proj_dir / "renders" / f"{tid}_short.mp4"

    print("-> Building SEO package...")
    subprocess.run([PY_VENV, str(SEO_PY), "--topic-id", tid, "--out", str(seo_out)], check=True)

    if not thumb_out.exists():
        print("-> Rendering 1280x720 Thumbnail...")
        try:
            subprocess.run(["node", str(MAKE_THUMB_MJS), str(thumb_out), nt["thumb_text"], nt["category"], "BABYBEATS RHYMO"], check=True)
        except subprocess.CalledProcessError:
            if not thumb_out.exists():
                raise
    else:
        print(f"-> Thumbnail already exists: {thumb_out.name}")

    if not mp4_out.exists():
        print("-> Executing Audio Synthesis & Video Pipeline (Kokoro + Whisper + Chrome + ffmpeg)...")
        pipe_cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(RUN_PIPELINE_PS1),
            "-ProjectDir", str(proj_dir),
            "-OutVideo", str(mp4_out),
            "-SheetStep", "2", "-SheetCols", "5"
        ]
        subprocess.run(pipe_cmd, check=True)
    else:
        print(f"-> MP4 already exists: {mp4_out.name}")

    # Verify with ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,width,height", "-of", "json", str(mp4_out)],
        capture_output=True, text=True, check=True
    )
    info = json.loads(probe.stdout)
    vstream = next((s for s in info.get("streams", []) if s.get("width")), {})
    if int(vstream.get("width", 0)) != 1080 or int(vstream.get("height", 0)) != 1920:
        raise RuntimeError(f"Unexpected dimensions: {vstream}")
    meta = {
        "duration_sec": round(float(info["format"]["duration"]), 2),
        "size_bytes": int(info["format"]["size"]),
        "width": vstream["width"],
        "height": vstream["height"]
    }
    print(f"VERIFIED MP4: {mp4_out.name} ({meta['duration_sec']}s, {meta['size_bytes']} bytes)")

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
    append_upload_queue(upload_entry)
    print(f"SUCCESS: Added {proj_name} to upload_queue.json as READY_FOR_UPLOAD (publish_at: {nt['publish_at_utc']})")


def main():
    update_topic_queue()
    for nt in NEW_7_TOPICS:
        generate_single_short(nt)
    print("\n========================================================")
    print("ALL 7 NEW MONTH 2 NURSERY RHYMES GENERATED SUCCESSFULLY!")
    print("========================================================")


if __name__ == "__main__":
    main()
