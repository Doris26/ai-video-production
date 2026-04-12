#!/usr/bin/env python3
"""
Full 15 scenes via Seedream 4.5 with reference_image for face consistency.
Uses ASSET_GIRL as reference + "NOT cartoon" prompt style.
"""
import json, time, base64, os
from urllib.request import Request, urlopen, urlretrieve
from PIL import Image
from pathlib import Path
import io

ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"
OUT = Path("/tmp/keiko_seedream_final")
OUT.mkdir(parents=True, exist_ok=True)

# Load girl face reference
img = Image.open("/tmp/ASSET_GIRL.png").resize((512, 512))
buf = io.BytesIO()
img.save(buf, format="PNG")
GIRL_B64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

# ═══════════════════════════════════════════════════════
# FIXED ASSETS
# ═══════════════════════════════════════════════════════

STYLE = "3D建模脸 style, hyper-realistic 3D CG render, NOT cartoon, NOT Disney, NOT Pixar, NOT chibi, semi-realistic anime, Unreal Engine 5 quality, 8K, cinematic lighting"

GIRL = "this same beautiful young Japanese woman aged 24, wispy messy bangs, long flowing dark brown hair, large sparkling dark brown eyes with detailed iris, smooth porcelain skin, natural subtle blush, small delicate nose, glossy pink lips"

BOY = "a tall intimidating Japanese male student aged 18, short spiky jet-black hair, sharp narrow dark eyes, strong jawline, wearing dark navy school uniform gakuran with collar unbuttoned"

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard on front wall, raised wooden teaching platform, tall windows with white curtains and warm golden afternoon sunlight, cream walls, fluorescent lights, polished wooden floor"

# ═══════════════════════════════════════════════════════
# 15 SCENES
# ═══════════════════════════════════════════════════════

SCENES = {
    "01_ENTRANCE": f"{STYLE}. Wide shot. {GIRL} walking through school gate in morning sunlight, wearing gray suit jacket over white blouse and pencil skirt, black heels, carrying briefcase, hair flowing in breeze, cherry blossoms floating, students turning to look. Tree-lined path to Japanese school.",

    "02_TEACHING": f"{STYLE}. Medium shot. {GIRL} standing on raised wooden teaching platform, holding open textbook, wearing gray suit, white blouse, pencil skirt, writing on green chalkboard with chalk, warm professional smile, golden afternoon light. {CLASSROOM}.",

    "03_CLOSEUP": f"{STYLE}. Close-up portrait. {GIRL} at classroom podium, looking directly at viewer, warm intelligent eyes, holding chalk, wearing gray suit and white blouse, pearl earring, soft afternoon light on porcelain skin. Blurred green chalkboard background.",

    "04_CONFRONTATION": f"{STYLE}. Medium two-shot. On the left: {GIRL} wearing gray suit, arms crossed, stern angry expression. On the right: {BOY} looking defiant, hands in pockets, cold smirk. Face to face between rows of wooden desks, tense, dramatic side lighting. {CLASSROOM}.",

    "05_CONFRONTATION_WIDE": f"{STYLE}. Wide shot. On left: {GIRL} in gray suit standing on teaching platform pointing angrily. On right: {BOY} sitting at desk smirking. Afternoon light from windows casting shadows on wooden floor. {CLASSROOM}.",

    "06_AFTER_SCHOOL": f"{STYLE}. Medium shot. {GIRL} sitting at teacher desk grading papers, gray suit jacket unbuttoned, white blouse loosened, reading glasses, tired but dedicated, warm desk lamp and fading sunset from windows, empty classroom. {CLASSROOM}.",

    "07_HALLWAY": f"{STYLE}. Cinematic medium shot from behind. {GIRL} walking down long empty school hallway toward classroom door, wearing gray suit and black heels, heels echoing, hair flowing, nervous clenched fist, late afternoon shadows on floor. Empty school hallway, shoe lockers, dimming light.",

    "08_SHOCK": f"{STYLE}. Close-up reaction. {GIRL} face expressing shock and fear, eyes wide, hand covering mouth, standing in doorway, harsh light from inside contrasting dark hallway. Classroom visible through door.",

    "09_VULNERABLE": f"{STYLE}. Emotional medium shot. {GIRL} sitting on wooden classroom floor, back against chalkboard, knees drawn to chest, arms hugging legs, hair falling over face, wearing wrinkled white blouse with sleeves rolled up, gray skirt, shoes off beside her, exhausted sad watery eyes. {CLASSROOM}, dim light.",

    "10_CRYING": f"{STYLE}. Close-up emotional portrait. {GIRL} with glistening watery eyes, single tear on porcelain cheek, wispy bangs on forehead, biting lip, deep sadness, wearing wrinkled white blouse, disheveled hair covering face, warm golden backlight from window. Blurred classroom background.",

    "11_POWERPLAY": f"{STYLE}. Low angle dramatic shot. Below left: {GIRL} sitting on classroom floor looking up frightened, wrinkled blouse, disheveled hair, tears. Above right: {BOY} standing tall with arms crossed looking down coldly, casting shadow over her. Side lighting from windows. {CLASSROOM}.",

    "12_MORNING": f"{STYLE}. Warm morning shot. {GIRL} standing at classroom window looking outside, melancholy expression, fresh gray suit and white blouse, holding coffee cup, morning golden sunlight streaming through window on her face and hair, alone in empty classroom. {CLASSROOM}.",

    "13_BRAVE_FACE": f"{STYLE}. Medium shot. {GIRL} at teaching platform attempting to teach, holding textbook, gray suit, forced smile hiding turmoil, slight dark circles under eyes, afternoon light. {CLASSROOM}, students at desks in background.",

    "14_DETERMINATION": f"{STYLE}. Dramatic close-up portrait. {GIRL} with determined fierce expression, jaw set, sparkling eyes showing inner strength, wispy bangs framing face, afternoon golden light catching in eyes, wearing gray suit, composed and strong. Blurred classroom window with light, bokeh.",

    "15_WALKING_AWAY": f"{STYLE}. Wide cinematic shot from behind. {GIRL} walking down tree-lined school path toward sunset, gray suit, briefcase, hair flowing in evening breeze, cherry blossom petals falling, solitary, golden hour light. School grounds, tree path, sunset sky.",
}

def post(body):
    r = Request(f"{ARK}/images/generations", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

print(f"{'='*60}")
print(f"  Keiko Full Story — Seedream 4.5 + reference_image")
print(f"{'='*60}")

for name, prompt in SCENES.items():
    print(f"\n[{name}]")
    for attempt in range(3):
        try:
            r = post({
                "model": "doubao-seedream-4-5-251128",
                "prompt": prompt,
                "reference_image": GIRL_B64,
                "response_format": "url",
                "size": "1920x1920"
            })
            url = r["data"][0]["url"]
            urlretrieve(url, str(OUT / f"{name}.png"))
            print(f"  OK")
            break
        except Exception as e:
            err = e.read().decode()[:150] if hasattr(e, 'read') else str(e)[:100]
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"  FAILED: {err}")

print(f"\n{'='*60}")
print(f"  DONE! {OUT}/")
print(f"{'='*60}")
