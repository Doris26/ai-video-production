#!/usr/bin/env python3
"""Full 15 scenes via Gemini 2.5 Flash Image API with reference_image for face consistency."""
import json, base64, time, os
from urllib.request import Request, urlopen
from pathlib import Path
from PIL import Image
import io

KEY = "AIzaSyBR3gI5L9ART4tI6io9qgwsLngUquZKUaQ"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={KEY}"
OUT = Path("/tmp/keiko_gemini")
OUT.mkdir(parents=True, exist_ok=True)

# Load girl face reference as base64 for Gemini
img = Image.open("/tmp/ASSET_GIRL.png").resize((512, 512))
buf = io.BytesIO()
img.save(buf, format="PNG")
GIRL_B64 = base64.b64encode(buf.getvalue()).decode()

STYLE = "3D建模脸 style, hyper-realistic 3D CG render, NOT cartoon, NOT Disney, NOT Pixar, semi-realistic anime, Unreal Engine 5 quality, 8K, cinematic lighting"

GIRL = "this same beautiful young Japanese woman from the reference image, aged 24, wispy messy bangs, long flowing dark brown hair, large sparkling dark brown eyes, smooth porcelain skin with subtle blush, small delicate nose, glossy pink lips"

BOY = "a tall intimidating Japanese male student aged 18, short spiky jet-black hair, sharp narrow dark eyes, strong jawline, wearing dark navy school uniform gakuran"

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard on front wall, raised wooden teaching platform, tall windows with white curtains and warm golden afternoon sunlight, cream walls, fluorescent lights, polished wooden floor"

SCENES = {
    "01_ENTRANCE": f"{STYLE}. Wide shot. {GIRL} walking through school gate in morning sunlight, wearing gray suit jacket over white blouse and pencil skirt, black heels, carrying briefcase, hair flowing in breeze, cherry blossoms floating, students in background. Tree-lined path to Japanese school.",

    "02_TEACHING": f"{STYLE}. Medium shot. {GIRL} standing on raised wooden teaching platform, holding open textbook, wearing gray suit, white blouse, pencil skirt, writing on green chalkboard, warm professional smile, golden afternoon light. {CLASSROOM}.",

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

def generate(prompt, outpath):
    body = json.dumps({
        "contents": [{"parts": [
            {"inlineData": {"mimeType": "image/png", "data": GIRL_B64}},
            {"text": f"Using this face as reference, generate an image: {prompt}"}
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }).encode()

    r = Request(URL, data=body, headers={"Content-Type": "application/json"})
    resp = urlopen(r, timeout=120)
    d = json.loads(resp.read())
    parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in parts:
        if "inlineData" in p:
            img_data = base64.b64decode(p["inlineData"]["data"])
            with open(outpath, "wb") as f:
                f.write(img_data)
            return len(img_data) // 1024
    return 0

print("=" * 60)
print("  Keiko Full Story — Gemini 2.5 Flash Image + Face Reference")
print("=" * 60)

for name, prompt in SCENES.items():
    print(f"\n[{name}]")
    for attempt in range(3):
        try:
            kb = generate(prompt, str(OUT / f"{name}.png"))
            if kb > 0:
                print(f"  OK {kb}KB")
                break
            else:
                print(f"  No image returned, retrying...")
        except Exception as e:
            err = e.read().decode()[:150] if hasattr(e, 'read') else str(e)[:100]
            print(f"  Error: {err}")
            if attempt < 2:
                time.sleep(5)
                continue
            print(f"  FAILED")
    time.sleep(2)  # Rate limit

print(f"\n{'=' * 60}")
print(f"  DONE! {OUT}/")
print(f"{'=' * 60}")
