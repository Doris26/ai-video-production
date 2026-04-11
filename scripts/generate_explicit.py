#!/usr/bin/env python3
"""
Keiko EXPLICIT scenes — ComfyUI xxmix_sdxl + IP-Adapter.
These are scenes that Seedream blocks. Uses same ASSETS for consistency.
"""
import json, time, urllib.request, urllib.parse, uuid, os

COMFYUI = "http://127.0.0.1:7860"
CID = str(uuid.uuid4())
CKPT = "xxmix_sdxl.safetensors"
IPA_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
OUT = "/tmp/keiko_explicit"
os.makedirs(OUT, exist_ok=True)

STYLE = "Donghua 3D CG animation style, semi-realistic anime, Unreal Engine 5 render, 8K ultra detailed, cinematic"

GIRL = "a beautiful young Japanese woman aged 24, 3D manga face, wispy messy bangs, long flowing dark brown hair, very large sparkling dark brown eyes, smooth porcelain skin with soft blush, small nose, glossy pink lips"

BOY = "a tall Japanese male student aged 18, short spiky black hair, sharp narrow eyes, strong jawline, wearing dark navy school uniform gakuran"

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard at front wall, raised wooden teaching platform, tall windows with white curtains and afternoon sunlight, cream walls, wooden floor"

NEG_NSFW = "ugly, deformed, bad anatomy, bad hands, missing fingers, extra fingers, blurry, low quality, watermark, text, logo, gray background, studio background, plain background, suit, jacket, blazer, formal wear, fully clothed"

SCENES = {
    # Stripping scene - on teaching platform
    "EX01_STRIP_STANDING": f"""{STYLE}. Full body shot.
{GIRL} standing on raised wooden teaching platform, topless, exposed large breasts with pink nipples, wearing only black sheer lace panties and black high heels, arms raised behind head with hands on neck, legs spread apart, flushed face looking down in shame, sweat on skin, NSFW.
{CLASSROOM}""",

    "EX02_STRIP_TURNING": f"""{STYLE}. Full body shot from side angle.
{GIRL} standing on raised wooden teaching platform, topless, breasts visible from side, wearing only black sheer panties, one arm covering chest shyly, other arm at side, looking away embarrassed, long hair covering part of face, warm afternoon light, NSFW.
{CLASSROOM}""",

    # Tied up scene
    "EX03_BOUND_FRAME": f"""{STYLE}. Medium shot.
{GIRL} bound with rope to metal exercise pull-up frame in classroom, wrists tied to top bar, topless, exposed breasts with nipples, legs spread and knees tied to frame base, wearing only white panties, blushing deeply, eyes squeezed shut in shame, sweat on skin, NSFW.
{CLASSROOM}""",

    "EX04_BOUND_CLOSEUP": f"""{STYLE}. Close-up shot.
{GIRL} face and upper body, bound with rope, topless, exposed breasts, tears streaming down cheeks, expression of humiliation and fear, rope marks on wrists, sweat glistening, wispy bangs stuck to forehead, NSFW.
{CLASSROOM} blurred in background""",

    # Desk scene
    "EX05_DESK_BENT": f"""{STYLE}. Medium shot from side.
{GIRL} bent over wooden teacher desk, topless, breasts pressed against desk surface, wearing only black panties pulled down to thighs, long hair spread across desk, face turned to side showing tears and blush, gripping edge of desk, afternoon light, NSFW.
{CLASSROOM}""",

    "EX06_DESK_LYING": f"""{STYLE}. Medium shot from above.
{GIRL} lying on back on wooden teacher desk, completely nude, covering breasts with one arm, other arm draped over eyes hiding face, legs dangling off edge, long hair spread on desk, flushed skin, tears visible, afternoon light on body, NSFW.
{CLASSROOM}""",

    # Floor scene
    "EX07_FLOOR_CURLED": f"""{STYLE}. Medium shot.
{GIRL} curled up on wooden classroom floor completely nude, knees drawn to chest, arms hugging legs, long hair covering body partially, face buried in knees, shaking, sweat and tears, dim evening light from windows, NSFW.
{CLASSROOM}""",

    # With boy - aftermath
    "EX08_AFTERMATH_COUPLE": f"""{STYLE}. Wide shot.
On the left: {GIRL} lying on wooden classroom floor completely exhausted and nude, covered only by torn white blouse draped over body, long disheveled hair spread on floor, tears and sweat, eyes closed.
On the right: {BOY} sitting at desk nearby fully clothed, cold indifferent expression, smoking.
Night scene, harsh fluorescent lighting, NSFW.
{CLASSROOM}""",
}

def queue(wf):
    d = json.dumps({"prompt": wf, "client_id": CID}).encode()
    r = urllib.request.Request(f"{COMFYUI}/prompt", data=d, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r).read())["prompt_id"]

def wait(pid, t=300):
    s = time.time()
    while time.time()-s < t:
        try:
            r = urllib.request.urlopen(f"{COMFYUI}/history/{pid}")
            h = json.loads(r.read())
            if pid in h:
                o = h[pid].get("outputs", {})
                st = h[pid].get("status", {})
                if st.get("completed") or st.get("status_str") == "success" or o:
                    return o
                if st.get("status_str") == "error":
                    return None
        except: pass
        time.sleep(3)
    return None

def dl_img(fn, sf, tp, sp):
    p = urllib.parse.urlencode({"filename": fn, "subfolder": sf, "type": tp})
    urllib.request.urlretrieve(f"{COMFYUI}/view?{p}", sp)
    print(f"  Saved: {sp}")

def get_img(outputs):
    for nid, no in outputs.items():
        if "images" in no:
            for im in no["images"]:
                return im["filename"], im.get("subfolder", ""), im.get("type", "output")
    return None, None, None

def build_solo(prompt, neg, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "10": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": IPA_MODEL}},
        "11": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": CLIP_VISION}},
        "12": {"class_type": "LoadImage", "inputs": {"image": "keiko_ref.png"}},
        "13": {"class_type": "PrepImageForClipVision", "inputs": {"image": ["12", 0], "interpolation": "LANCZOS", "crop_position": "center", "sharpening": 0.0}},
        "14": {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["1", 0], "ipadapter": ["10", 0], "image": ["13", 0],
            "weight": 0.5, "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 0.8, "embeds_scaling": "V only",
            "clip_vision": ["11", 0],
        }},
        "30": {"class_type": "KSampler", "inputs": {
            "model": ["14", 0], "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0
        }},
        "31": {"class_type": "VAEDecode", "inputs": {"samples": ["30", 0], "vae": ["1", 2]}},
        "32": {"class_type": "SaveImage", "inputs": {"images": ["31", 0], "filename_prefix": "explicit"}},
    }

print("="*60)
print("  Keiko EXPLICIT Scenes — ComfyUI xxmix_sdxl + IP-Adapter")
print("="*60)

seed = 100001
for name, prompt in SCENES.items():
    print(f"\n[{name}]")
    wf = build_solo(prompt, NEG_NSFW, seed)
    pid = queue(wf)
    o = wait(pid, 300)
    if o:
        fn, sf, tp = get_img(o)
        if fn: dl_img(fn, sf, tp, f"{OUT}/{name}.png")
    else:
        print("  FAILED")
    seed += 1

print(f"\n{'='*60}\nDONE!\n{'='*60}")
