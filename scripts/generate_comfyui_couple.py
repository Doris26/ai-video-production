#!/usr/bin/env python3
"""Couple scenes: girl IP-Adapter FULL (no mask) + prompt-only boy."""
import json, time, urllib.request, urllib.parse, uuid, os

COMFYUI = "http://127.0.0.1:7860"
CID = str(uuid.uuid4())
CKPT = "xxmix_sdxl.safetensors"
IPA_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
OUT = "/tmp/keiko_couple_v3"
os.makedirs(OUT, exist_ok=True)

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard at front wall, raised wooden teaching platform, tall windows on left wall with white curtains and warm afternoon sunlight, cream-colored walls, fluorescent ceiling lights, polished wooden floor"
NEG = "ugly, deformed, bad anatomy, bad hands, missing fingers, extra fingers, blurry, low quality, watermark, text, logo, gray background, studio background, plain background, solo, single person, two girls, 2girls"
NEG_DISH = NEG + ", neat clothes, pristine, tidy"

GIRL = "a beautiful young Japanese woman aged 24 with wispy messy bangs and long flowing dark brown hair, very large sparkling dark brown eyes, smooth porcelain skin with soft blush, small delicate nose, glossy pink lips, 3D CG manga face"
BOY = "a tall Japanese male student aged 18 with short spiky black hair, sharp narrow eyes, strong jawline, wearing dark navy school uniform gakuran"

SCENES = {
    "B1_CONFRONTATION": {
        "prompt": f"2people, 1boy 1girl, medium shot, on the left {GIRL} wearing gray suit with arms crossed looking stern and angry, on the right {BOY} looking defiant with hands in pockets, standing face to face between rows of wooden desks, tense confrontation, afternoon light, 3D CG anime style, semi-realistic face, high detail, cinematic. {CLASSROOM}",
        "neg": NEG, "seed": 90001,
    },
    "B2_WIDE": {
        "prompt": f"2people, 1boy 1girl, wide shot, on the left {GIRL} wearing gray suit standing on raised teaching platform pointing angrily, on the right {BOY} sitting at wooden desk smirking, dramatic afternoon light from tall windows casting shadows, 3D CG anime style, semi-realistic face, cinematic. {CLASSROOM}",
        "neg": NEG, "seed": 90002,
    },
    "D1_AFTERMATH": {
        "prompt": f"2people, 1boy 1girl, medium shot, on the left {GIRL} with disheveled hair lying on wooden classroom floor exhausted wearing torn open white blouse, tears and sweat on face, on the right {BOY} standing over her with arms crossed cold expression, nighttime fluorescent lighting, 3D CG anime style, semi-realistic face, emotional, cinematic. {CLASSROOM}, dark night outside windows",
        "neg": NEG_DISH, "seed": 90003,
    },
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

def build(prompt, neg, seed, gw):
    """Girl-only IP-Adapter, NO mask, full image. Boy from prompt only."""
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
            "weight": gw, "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 0.8, "embeds_scaling": "V only",
            "clip_vision": ["11", 0],
        }},
        "30": {"class_type": "KSampler", "inputs": {
            "model": ["14", 0], "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0
        }},
        "31": {"class_type": "VAEDecode", "inputs": {"samples": ["30", 0], "vae": ["1", 2]}},
        "32": {"class_type": "SaveImage", "inputs": {"images": ["31", 0], "filename_prefix": "couple_v3"}},
    }

# Test different girl weights
WEIGHTS = [0.35, 0.5, 0.6]

print("="*50)
print("Couple V3: Girl IP-Adapter FULL (no mask), boy from prompt")
print("="*50)

for name, cfg in SCENES.items():
    for gw in WEIGHTS:
        label = f"{name}_gw{int(gw*100):02d}"
        print(f"\n[{label}] girl_weight={gw}")
        wf = build(cfg["prompt"], cfg["neg"], cfg["seed"], gw)
        pid = queue(wf)
        o = wait(pid, 300)
        if o:
            fn, sf, tp = get_img(o)
            if fn: dl_img(fn, sf, tp, f"{OUT}/{label}.png")
        else:
            print("  FAILED")

print(f"\nDONE!")
