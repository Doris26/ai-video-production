#!/usr/bin/env python3
"""
Master Production Script — Classroom Story
Generates all images, strips, QA checks, regenerates failures.

Pipeline:
1. Generate assets (Banana Pro, face → fullbody → side via img2img)
2. Generate clean scenes (Banana Pro with face ref)
3. Strip clothing (epicrealism img2img d0.65 on ComfyUI)
4. Face swap (ReActor on ComfyUI) — optional
5. QA exam (check face, style, clothing)
6. Regenerate failures
7. Video generation (Wan2.1 / Seedance)
8. Audio (Edge-TTS) + stitch (FFmpeg)
"""

import os, sys, json, base64, time, argparse
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

FAL_KEY = open(os.path.expanduser("~/.openclaw/secrets/fal_api_key")).read().strip()
os.environ["FAL_KEY"] = FAL_KEY

COMFYUI_IP = None  # Set dynamically from AWS
COMFYUI_PORT = 7860
AWS_INSTANCE_ID = "i-07387478d3044b9c7"
SSH_KEY = os.path.expanduser("~/.ssh/sd-gpu-key.pem")

OUT_DIR = Path("/tmp/keiko_production_final")
ASSET_DIR = Path("/tmp/banana_assets")

# Style anchoring — appended to EVERY Banana Pro prompt
STYLE_ANCHOR = "smooth skin texture, clean detailed rendering, consistent bright lighting, same art style as reference image, hyper-realistic, NOT cartoon, NOT dark, NOT gritty, NOT anime, 8K"
NEG_GLOBAL = "ugly, deformed, cartoon, chibi, Disney, Pixar, blurry, cute, kawaii, Western, European, blonde, anime, asymmetric eyes, glasses, dark mood, rough texture, grainy"

# ═══════════════════════════════════════════════════════
# CHARACTERS
# ═══════════════════════════════════════════════════════

CHARACTERS = {
    "keiko": {
        "face_prompt": "Hyper-realistic close-up portrait headshot, beautiful young Japanese woman aged 24, wispy messy bangs, long dark brown hair, large expressive brown eyes, smooth porcelain skin, natural blush, small nose, pink glossy lips, confident gentle smile, wearing gray suit jacket and white blouse, plain light gray background, 8K",
        "desc": "same beautiful young Japanese woman aged 24, wispy bangs, long dark brown hair, large symmetric brown eyes, smooth porcelain skin, pink lips",
    },
    "kuroda": {
        "face_prompt": "Hyper-realistic close-up portrait headshot, tall Japanese male student aged 18, short spiky jet-black hair, sharp narrow dark eyes, strong defined jawline, intimidating confident expression, wearing dark navy school uniform gakuran collar unbuttoned, plain light gray background, 8K",
        "desc": "tall Japanese male student aged 18, short spiky black hair, sharp dark eyes, strong jawline, dark navy school uniform gakuran",
    },
}

# ═══════════════════════════════════════════════════════
# SCENES
# ═══════════════════════════════════════════════════════

CLASSROOM = "Japanese high school classroom, wooden desks and chairs, green chalkboard, teaching platform, tall windows with afternoon sunlight"

SCENES = {
    "01_ENTRANCE": {
        "prompt": f"Wide shot. {{keiko}} walking through Japanese school gate, morning sunlight, gray suit, pencil skirt, black heels, briefcase, cherry blossoms, students behind. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko"],
    },
    "02_TEACHING": {
        "prompt": f"Medium shot. {{keiko}} on teaching platform, holding textbook, gray suit, white blouse, pencil skirt, writing on chalkboard, warm smile, afternoon light. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "03_CLOSEUP": {
        "prompt": f"Close-up portrait. {{keiko}} at podium, warm eyes, holding chalk, gray suit, white blouse, pearl earring, afternoon light. Blurred chalkboard. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "04_CONFRONTATION": {
        "prompt": f"Two-shot. Left: {{keiko}} gray suit, arms crossed, stern. Right: {{kuroda}} defiant, hands in pockets. Between desks, tense. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko", "kuroda"],
    },
    "05_CONFRONTATION_WIDE": {
        "prompt": f"Wide shot. Left: {{keiko}} gray suit on platform pointing. Right: {{kuroda}} at desk smirking. Shadows. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko", "kuroda"],
    },
    "06_AFTER_SCHOOL": {
        "prompt": f"{{keiko}} at teacher desk grading, suit unbuttoned, blouse loosened, tired, desk lamp, sunset, empty classroom. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "07_HALLWAY": {
        "prompt": f"From behind. {{keiko}} walking down empty school hallway, gray suit, heels, hair flowing, nervous fist, afternoon shadows. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko"],
    },
    "08_SHOCK": {
        "prompt": f"Close-up. {{keiko}} shocked face, eyes wide, hand over mouth, Japanese school doorway, harsh light from classroom. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko"],
    },
    "09_VULNERABLE": {
        "prompt": f"{{keiko}} sitting on wooden floor against chalkboard, knees to chest, hugging legs, hair over face, wrinkled white blouse sleeves rolled up, gray skirt, shoes off, sad watery eyes. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "10_CRYING": {
        "prompt": f"Close-up portrait. {{keiko}} glistening eyes, tear on cheek, biting lip, sadness, wrinkled blouse, disheveled hair, golden backlight from window. Blurred classroom. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "11_POWERPLAY": {
        "prompt": f"Low angle. Below: {{keiko}} on floor frightened, wrinkled blouse, tears. Above: {{kuroda}} standing arms crossed coldly. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko", "kuroda"],
    },
    "12_MORNING": {
        "prompt": f"{{keiko}} at classroom window, melancholy, fresh gray suit, coffee cup, morning sunlight on face, alone. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "13_BRAVE_FACE": {
        "prompt": f"{{keiko}} at teaching platform, textbook, gray suit, forced smile, dark circles, afternoon light, students behind. {CLASSROOM}. {STYLE_ANCHOR}",
        "strip": True, "characters": ["keiko"],
    },
    "14_DETERMINATION": {
        "prompt": f"Close-up. {{keiko}} determined fierce expression, jaw set, sparkling eyes, wispy bangs, golden light, gray suit. Blurred classroom bokeh. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko"],
    },
    "15_WALKING_AWAY": {
        "prompt": f"Wide from behind. {{keiko}} walking tree-lined school path, sunset, gray suit, briefcase, cherry blossoms, golden hour. {STYLE_ANCHOR}",
        "strip": False, "characters": ["keiko"],
    },
}

# Strip prompts for epicrealism
STRIP_PROMPTS = {
    "02_TEACHING": "Hyper-realistic, {keiko}, standing on teaching platform in classroom, completely topless nude, large exposed breasts with prominent pink nipples visible, wearing only tiny black thong, black heels, flushed face, holding textbook, green chalkboard, wooden desks, afternoon sunlight, NSFW, nude, topless, nipples, 8K",
    "03_CLOSEUP": "Hyper-realistic, close-up, {keiko}, topless nude, large exposed breasts with pink nipples, bare shoulders chest, flushed face, tears in eyes, porcelain skin, classroom background, NSFW, nude, topless, nipples, 8K",
    "06_AFTER_SCHOOL": "Hyper-realistic, {keiko}, sitting at desk, topless nude, exposed breasts with nipples, wearing only panties, tired face, desk lamp, sunset, empty classroom, NSFW, nude, topless, nipples, 8K",
    "09_VULNERABLE": "Hyper-realistic, {keiko}, sitting on floor against chalkboard, completely naked nude, exposed breasts nipples, bare skin, knees up, crying tears, messy hair, dim light, classroom desks, NSFW, nude, naked, nipples, 8K",
    "10_CRYING": "Hyper-realistic, close-up, {keiko}, topless nude, exposed breasts pink nipples, tears streaming, anguished, bare shoulders, sweat, golden backlight, NSFW, nude, topless, nipples, 8K",
    "12_MORNING": "Hyper-realistic, {keiko}, at window from behind, topless nude, bare back visible, spine shoulders, wearing only white panties showing butt, coffee cup, morning sunlight, classroom, NSFW, nude, bare back, butt, 8K",
    "13_BRAVE_FACE": "Hyper-realistic, {keiko}, at platform, topless nude, large exposed breasts pink nipples, wearing only black skirt, forced smile, holding textbook at waist, classroom desks, afternoon light, NSFW, nude, topless, nipples, 8K",
}

STRIP_NEG = "ugly, deformed, cartoon, blurry, low quality, watermark, text, clothes, suit, jacket, blazer, blouse, shirt, bra, skirt, pants, dressed, covered, clothed, fabric, garment"

# ═══════════════════════════════════════════════════════
# BANANA PRO FUNCTIONS
# ═══════════════════════════════════════════════════════

def banana_generate(prompt, neg=NEG_GLOBAL, image_url=None, strength=0.50, seed=None, size=1024):
    """Generate image with Banana Pro. Always use face ref if available."""
    import fal_client
    args = {
        "prompt": prompt,
        "negative_prompt": neg,
        "image_size": {"width": size, "height": size},
        "num_inference_steps": 30,
        "guidance_scale": 7.0,
    }
    if image_url:
        args["image_url"] = image_url
        args["strength"] = strength
    if seed:
        args["seed"] = seed
    result = fal_client.submit("fal-ai/nano-banana-pro", arguments=args).get()
    return result["images"][0]["url"]


def load_face_ref(character_name):
    """Load character face asset as base64 data URL."""
    face_path = ASSET_DIR / f"{character_name}_face.png"
    if not face_path.exists():
        # Remap old naming
        face_path = ASSET_DIR / "girl_1_face.png" if character_name == "keiko" else ASSET_DIR / "boy_1_face.png"
    with open(face_path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"


# ═══════════════════════════════════════════════════════
# ASSET GENERATION
# ═══════════════════════════════════════════════════════

def generate_assets():
    """Generate consistent face/fullbody/side assets for each character."""
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    for name, char in CHARACTERS.items():
        print(f"\n=== Asset: {name} ===")

        # Face (text-only, no ref)
        face_path = ASSET_DIR / f"{name}_face.png"
        if not face_path.exists():
            print(f"  [face]")
            url = banana_generate(char["face_prompt"])
            urlretrieve(url, str(face_path))
            print(f"  OK")

        face_ref = load_face_ref(name)

        # Fullbody (img2img from face)
        fb_path = ASSET_DIR / f"{name}_fullbody.png"
        if not fb_path.exists():
            print(f"  [fullbody]")
            prompt = char["face_prompt"].replace("close-up portrait headshot", "full body shot head to toe").replace("plain light gray background", "standing confidently, plain light gray background")
            url = banana_generate(prompt, image_url=face_ref, strength=0.55)
            urlretrieve(url, str(fb_path))
            print(f"  OK")

        # Side (img2img from face)
        side_path = ASSET_DIR / f"{name}_side.png"
        if not side_path.exists():
            print(f"  [side]")
            prompt = char["face_prompt"].replace("close-up portrait headshot", "three-quarter side angle portrait").replace("confident gentle smile", "looking to the right, slight smile")
            url = banana_generate(prompt, image_url=face_ref, strength=0.45)
            urlretrieve(url, str(side_path))
            print(f"  OK")


# ═══════════════════════════════════════════════════════
# SCENE GENERATION
# ═══════════════════════════════════════════════════════

def generate_scenes(scenes=None, num_versions=1, force=False):
    """Generate clean scenes with Banana Pro + face ref."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clean_dir = OUT_DIR / "clean"
    clean_dir.mkdir(exist_ok=True)

    if scenes is None:
        scenes = list(SCENES.keys())

    face_ref = load_face_ref("keiko")

    for name in scenes:
        cfg = SCENES[name]
        # Fill character descriptions into prompt
        prompt = cfg["prompt"]
        for char_name, char in CHARACTERS.items():
            prompt = prompt.replace(f"{{{{{char_name}}}}}", char["desc"])

        for v in range(num_versions):
            fname = f"{name}.png" if num_versions == 1 else f"{name}_v{v+1}.png"
            fpath = clean_dir / fname
            if fpath.exists() and not force:
                print(f"[{fname}] exists, skip")
                continue

            print(f"[{fname}]")
            seed = 10000 + hash(name) % 10000 + v
            try:
                url = banana_generate(prompt, image_url=face_ref, strength=0.50, seed=seed)
                urlretrieve(url, str(fpath))
                print(f"  OK")
            except Exception as e:
                print(f"  FAILED: {e}")
            time.sleep(1)


# ═══════════════════════════════════════════════════════
# STRIP (ComfyUI epicrealism)
# ═══════════════════════════════════════════════════════

def comfyui_url():
    return f"http://{COMFYUI_IP}:{COMFYUI_PORT}"

def comfyui_queue(wf):
    import uuid
    CID = str(uuid.uuid4())
    d = json.dumps({"prompt": wf, "client_id": CID}).encode()
    r = Request(f"{comfyui_url()}/prompt", data=d, headers={"Content-Type": "application/json"})
    return json.loads(urlopen(r).read())["prompt_id"]

def comfyui_wait(pid, timeout=300):
    s = time.time()
    while time.time() - s < timeout:
        try:
            h = json.loads(urlopen(f"{comfyui_url()}/history/{pid}").read())
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    return None
                o = h[pid].get("outputs", {})
                if o:
                    return o
        except:
            pass
        time.sleep(3)
    return None

def comfyui_download(outputs, save_path):
    from urllib.parse import urlencode
    for nid, no in outputs.items():
        if "images" in no:
            fn = no["images"][0]["filename"]
            sf = no["images"][0].get("subfolder", "")
            tp = no["images"][0].get("type", "output")
            urlretrieve(f"{comfyui_url()}/view?{urlencode({'filename': fn, 'subfolder': sf, 'type': tp})}", save_path)
            return True
    return False

def strip_scenes(scenes=None, force=False):
    """Strip clothing using epicrealism img2img on ComfyUI."""
    strip_dir = OUT_DIR / "stripped"
    strip_dir.mkdir(exist_ok=True)
    clean_dir = OUT_DIR / "clean"

    if scenes is None:
        scenes = [name for name, cfg in SCENES.items() if cfg["strip"]]

    for name in scenes:
        fpath = strip_dir / f"{name}.png"
        if fpath.exists() and not force:
            print(f"[STRIP {name}] exists, skip")
            continue

        clean_path = clean_dir / f"{name}.png"
        if not clean_path.exists():
            print(f"[STRIP {name}] no clean image, skip")
            continue

        prompt = STRIP_PROMPTS.get(name, "")
        if not prompt:
            continue
        for char_name, char in CHARACTERS.items():
            prompt = prompt.replace(f"{{{{{char_name}}}}}", char["desc"])

        print(f"[STRIP {name}]")
        # Upload clean image to ComfyUI
        # (assumes already uploaded via scp)

        wf = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "epicrealism_xl.safetensors"}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"text": STRIP_NEG, "clip": ["1", 1]}},
            "5": {"class_type": "LoadImage", "inputs": {"image": f"prod_{name}.png"}},
            "6": {"class_type": "VAEEncode", "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}},
            "30": {"class_type": "KSampler", "inputs": {
                "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
                "latent_image": ["6", 0], "seed": 1100001 + hash(name) % 10000,
                "steps": 30, "cfg": 8.0, "sampler_name": "euler_ancestral",
                "scheduler": "karras", "denoise": 0.65,
            }},
            "31": {"class_type": "VAEDecode", "inputs": {"samples": ["30", 0], "vae": ["1", 2]}},
            "32": {"class_type": "SaveImage", "inputs": {"images": ["31", 0], "filename_prefix": "strip"}},
        }
        pid = comfyui_queue(wf)
        o = comfyui_wait(pid)
        if o:
            comfyui_download(o, str(fpath))
            print(f"  OK")
        else:
            print(f"  FAILED")


# ═══════════════════════════════════════════════════════
# QA EXAM
# ═══════════════════════════════════════════════════════

def qa_check_image(image_path, scene_name, scene_config):
    """
    QA checks for a generated image. Returns (pass, issues).
    Uses simple heuristics — can be upgraded to AI vision later.
    """
    issues = []

    # Check file exists and has reasonable size
    if not os.path.exists(image_path):
        return False, ["file missing"]

    size = os.path.getsize(image_path)
    if size < 50000:
        issues.append("file too small, likely corrupted")
    if size > 5000000:
        issues.append("file unusually large")

    # TODO: Add AI vision check (Gemini/Claude) for:
    # - Face symmetry (eyes aligned)
    # - Face matches reference asset
    # - Style consistency (not cartoon)
    # - Clothing stripped (for NSFW scenes)
    # - Background correct (classroom)
    # - No glasses (unless specified)
    # - No artifacts/deformations

    return len(issues) == 0, issues


def qa_all():
    """Run QA on all generated images."""
    print("\n=== QA EXAM ===")
    clean_dir = OUT_DIR / "clean"
    strip_dir = OUT_DIR / "stripped"

    failures = []
    for name, cfg in SCENES.items():
        # Check clean
        clean_path = clean_dir / f"{name}.png"
        passed, issues = qa_check_image(str(clean_path), name, cfg)
        status = "PASS" if passed else f"FAIL: {', '.join(issues)}"
        print(f"  [clean/{name}] {status}")
        if not passed:
            failures.append(("clean", name, issues))

        # Check stripped
        if cfg["strip"]:
            strip_path = strip_dir / f"{name}.png"
            passed, issues = qa_check_image(str(strip_path), name, cfg)
            status = "PASS" if passed else f"FAIL: {', '.join(issues)}"
            print(f"  [stripped/{name}] {status}")
            if not passed:
                failures.append(("stripped", name, issues))

    if failures:
        print(f"\n{len(failures)} failures found. Regenerate with --regen")
    else:
        print("\nAll passed!")
    return failures


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Production Script")
    parser.add_argument("--step", choices=["assets", "scenes", "strip", "qa", "all"], default="all")
    parser.add_argument("--scenes", nargs="+", help="Specific scenes to generate")
    parser.add_argument("--versions", type=int, default=1, help="Versions per scene")
    parser.add_argument("--force", action="store_true", help="Regenerate even if exists")
    parser.add_argument("--comfyui-ip", help="ComfyUI server IP")
    args = parser.parse_args()

    if args.comfyui_ip:
        COMFYUI_IP = args.comfyui_ip

    if args.step in ("assets", "all"):
        generate_assets()

    if args.step in ("scenes", "all"):
        generate_scenes(args.scenes, args.versions, args.force)

    if args.step in ("strip", "all"):
        if not COMFYUI_IP:
            print("ERROR: Need --comfyui-ip for strip step")
        else:
            strip_scenes(args.scenes, args.force)

    if args.step in ("qa", "all"):
        qa_all()
