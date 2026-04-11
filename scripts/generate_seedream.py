#!/usr/bin/env python3
"""
Full Keiko classroom story — ALL non-explicit scenes via Seedream 4.5.
Uses fixed ASSETS for consistency. Explicit scenes marked for ComfyUI later.
"""
import json, time, os
from urllib.request import Request, urlopen
from pathlib import Path

ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"
OUT = Path("/tmp/keiko_full_story")
OUT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════
# FIXED ASSETS — identical in EVERY prompt for consistency
# ═══════════════════════════════════════════════════════

STYLE = "Donghua 3D CG animation style, semi-realistic anime, Unreal Engine 5 render, 8K ultra detailed, cinematic color grading, shallow depth of field"

GIRL_ASSET = """a beautiful young Japanese woman aged 24, 3D建模脸 manga face style, wispy messy bangs falling over forehead, long flowing dark brown hair past shoulders, very large sparkling dark brown eyes with double eyelids and long thick eyelashes, extremely smooth flawless porcelain skin with soft pink blush on cheeks, small delicate nose, full glossy pink coral lips, round face shape with small chin, intellectual beauty"""

BOY_ASSET = """a tall intimidating Japanese male student aged 18, short spiky jet-black hair, sharp narrow dark eyes with intense gaze, strong defined jawline, light stubble, athletic build, wearing dark navy school uniform gakuran with collar unbuttoned showing white shirt"""

SCENE_ASSET = """Japanese high school classroom: rows of wooden desks and chairs, large green chalkboard on front wall with chalk writing, raised wooden teaching platform in front of chalkboard, tall windows on left wall with white curtains and warm golden afternoon sunlight streaming in, cream-colored walls, fluorescent ceiling lights, polished wooden floor, clock on back wall, bookshelves along right wall"""

# ═══════════════════════════════════════════════════════
# 15 SCENES — matching story beats from 景子老师的课外授业
# Non-explicit scenes for Seedream, explicit ones marked [COMFYUI]
# ═══════════════════════════════════════════════════════

SCENES = {
    # Chapter 1 - Introduction
    "01_KEIKO_ENTRANCE": f"""{STYLE}. Wide establishing shot.
{GIRL_ASSET} walking through school gate in morning sunlight, wearing professional gray suit jacket over white blouse and pencil skirt, black high heels, carrying leather briefcase, long hair flowing in breeze, cherry blossom petals floating, students in background turning to look at her with admiration.
Background: tree-lined path leading to Japanese school building, morning golden light.""",

    "02_TEACHING": f"""{STYLE}. Medium shot.
{GIRL_ASSET} standing confidently on raised wooden teaching platform, holding open English textbook in left hand, right hand writing on green chalkboard with chalk, wearing gray suit jacket over white blouse, pencil skirt, warm professional smile, afternoon golden light from windows illuminating her face.
Background: {SCENE_ASSET}.""",

    "03_TEACHING_CLOSEUP": f"""{STYLE}. Close-up portrait shot.
{GIRL_ASSET} at classroom podium, looking directly at viewer with warm intelligent eyes, holding chalk, wearing gray suit and white blouse with collar, pearl earring visible, soft afternoon light creating warm glow on her porcelain skin.
Background: blurred green chalkboard with chalk writing, {SCENE_ASSET} out of focus.""",

    # Chapter 1 - Confrontation with Kuroda
    "04_CONFRONTATION": f"""{STYLE}. Medium two-shot.
On the left: {GIRL_ASSET} wearing gray suit, arms crossed, stern angry expression, brow furrowed.
On the right: {BOY_ASSET}, looking defiant with hands in pockets, cold smirk.
They stand face to face between rows of wooden desks, tense atmosphere, dramatic afternoon side lighting casting long shadows.
Background: {SCENE_ASSET}.""",

    "05_CONFRONTATION_WIDE": f"""{STYLE}. Wide establishing shot of full classroom.
On the left: {GIRL_ASSET} wearing gray suit, standing on raised teaching platform, pointing angrily with authority.
On the right: {BOY_ASSET}, sitting at wooden desk with arms crossed, smirking defiantly.
Dramatic afternoon light from tall windows casting long shadows across wooden floor, dust motes visible in sunbeams.
Background: {SCENE_ASSET}.""",

    # Chapter 1 - After school meeting
    "06_AFTER_SCHOOL": f"""{STYLE}. Medium shot, warm lighting.
{GIRL_ASSET} sitting at teacher's desk grading papers, wearing gray suit with jacket unbuttoned, white blouse slightly loosened, reading glasses on, looking tired but dedicated, warm desk lamp light mixed with fading sunset from windows, empty classroom.
Background: {SCENE_ASSET}, late afternoon, most desks empty, sunset orange light from windows.""",

    # Chapter 1 - Walking to classroom nervously
    "07_HALLWAY": f"""{STYLE}. Medium shot from behind, cinematic.
{GIRL_ASSET} walking down long empty school hallway toward classroom door at end, wearing gray suit and black heels, high heels echoing, long hair flowing behind her, nervous body language with clenched fist, late afternoon shadows stretching across floor.
Background: empty Japanese school hallway, shoe lockers on sides, dimming light through windows.""",

    # Chapter 1 - Discovering the situation
    "08_SHOCK": f"""{STYLE}. Close-up reaction shot.
{GIRL_ASSET} face expressing shock and fear, eyes wide open, mouth slightly agape, hand reaching up to cover mouth, standing in classroom doorway, dramatic harsh lighting from inside classroom contrasting with dark hallway.
Background: bright classroom light spilling into dark hallway, {SCENE_ASSET} visible through door.""",

    # Chapter 2 - Vulnerable
    "09_VULNERABLE": f"""{STYLE}. Medium emotional shot.
{GIRL_ASSET} sitting on wooden classroom floor with back against chalkboard, knees drawn up to chest, arms hugging knees, long hair falling over face like curtain, wearing wrinkled white blouse with sleeves rolled up and gray pencil skirt, shoes kicked off beside her, exhausted sad expression, watery eyes.
Background: {SCENE_ASSET}, late afternoon dim light.""",

    # Chapter 2 - Crying
    "10_CRYING": f"""{STYLE}. Close-up emotional portrait.
{GIRL_ASSET} with watery glistening eyes, a single tear rolling down porcelain cheek, wispy bangs stuck to forehead, biting lower lip, expression of deep sadness and despair, wearing wrinkled white blouse with collar loosened, disheveled hair partially covering face, warm golden backlight from window creating emotional halo.
Background: blurred {SCENE_ASSET}.""",

    # Chapter 2 - Kuroda standing over her
    "11_POWERPLAY": f"""{STYLE}. Low angle dramatic shot.
On the left below: {GIRL_ASSET} sitting on classroom floor looking up with frightened expression, wearing wrinkled white blouse, hair disheveled, tears on cheeks.
On the right above: {BOY_ASSET} standing tall over her with arms crossed, looking down coldly, dominant posture, casting shadow over her.
Dramatic side lighting from classroom windows, tense atmosphere.
Background: {SCENE_ASSET}.""",

    # Chapter 3 - Morning after
    "12_MORNING": f"""{STYLE}. Warm morning shot.
{GIRL_ASSET} standing at classroom window looking outside with melancholy expression, wearing fresh gray suit and white blouse, holding coffee cup, morning golden sunlight streaming through window illuminating her face and hair, contemplative mood, alone in empty classroom.
Background: {SCENE_ASSET}, early morning light, empty desks, quiet peaceful atmosphere.""",

    # Chapter 3 - Teaching again (brave face)
    "13_BRAVE_FACE": f"""{STYLE}. Medium shot.
{GIRL_ASSET} standing at teaching platform attempting to teach normally, holding textbook, wearing gray suit, forced smile hiding inner turmoil, slight dark circles under eyes, afternoon light.
Background: {SCENE_ASSET}, students seated at desks in background (shown from behind).""",

    # Final - Emotional close
    "14_DETERMINATION": f"""{STYLE}. Dramatic close-up portrait.
{GIRL_ASSET} with determined fierce expression, jaw set, sparkling eyes showing inner strength despite everything, wispy bangs framing face, afternoon golden light catching in her eyes, wearing gray suit looking composed and strong.
Background: blurred classroom window with afternoon light, {SCENE_ASSET} soft bokeh.""",

    # Final - Walking away
    "15_WALKING_AWAY": f"""{STYLE}. Wide cinematic shot from behind.
{GIRL_ASSET} walking away down tree-lined school path toward sunset, wearing gray suit and carrying briefcase, long hair flowing in evening breeze, cherry blossom petals falling, solitary figure, melancholy but resilient, golden hour sunset light.
Background: beautiful Japanese school grounds, tree-lined path, golden sunset sky.""",
}

def post(endpoint, body):
    r = Request(f"{ARK}/{endpoint}", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def dl(url):
    with urlopen(Request(url), timeout=300) as resp:
        return resp.read()

print(f"{'='*60}")
print(f"  Keiko Full Story — 15 Scenes via Seedream 4.5")
print(f"  Using fixed GIRL/BOY/SCENE assets")
print(f"{'='*60}")

for name, prompt in SCENES.items():
    print(f"\n[{name}]")
    for attempt in range(3):
        try:
            r = post("images/generations", {
                "model": "doubao-seedream-4-5-251128",
                "prompt": prompt,
                "response_format": "url",
                "size": "1920x1920"
            })
            url = r["data"][0]["url"]
            d = dl(url)
            p = OUT / f"{name}.png"
            p.write_bytes(d)
            print(f"  OK {len(d)//1024}KB")
            break
        except Exception as e:
            err = str(e)
            if hasattr(e, 'read'):
                err = e.read().decode()[:200]
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"  FAILED: {err}")

print(f"\n{'='*60}")
print(f"  DONE! {OUT}/")
print(f"{'='*60}")
