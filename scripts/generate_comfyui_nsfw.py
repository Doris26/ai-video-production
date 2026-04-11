#!/usr/bin/env python3
"""Re-run C2_EXPOSED with multiple IP-Adapter weights for comparison."""
import json, time, urllib.request, urllib.parse, uuid, os

COMFYUI = "http://127.0.0.1:7860"
CID = str(uuid.uuid4())
CKPT = "xxmix_sdxl.safetensors"
IPA_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
OUT = "/tmp/c2_rerun"
os.makedirs(OUT, exist_ok=True)

NEG = "ugly, deformed, bad anatomy, bad hands, missing fingers, extra fingers, blurry, low quality, watermark, text, logo, gray background, studio background, plain background, suit, jacket, blazer, formal wear, business suit"

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard at front wall, raised wooden teaching platform, tall windows on left wall with white curtains and warm afternoon sunlight, cream-colored walls, fluorescent ceiling lights, polished wooden floor"

PROMPT = f"1girl, full body shot, beautiful Japanese woman aged 24 standing on raised wooden teaching platform, topless, exposed breasts with pink nipples, wearing only black sheer panties and black high heels, arms raised behind head with hands on neck, legs spread apart wider than shoulders, flushed face looking down in shame, long black hair flowing down back, warm afternoon sunlight from windows, sweat glistening on skin, 3D CG anime style, semi-realistic face, NSFW, high detail, masterpiece. {CLASSROOM}, male students sitting on floor around the platform watching from below"

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
                    print(f"  ERROR: {json.dumps(st)[:200]}")
                    return None
        except: pass
        time.sleep(3)
    print("  TIMEOUT"); return None

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

def build_wf(prompt, neg, girl_weight, start_at, end_at, seed):
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "10": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": IPA_MODEL}},
        "11": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": CLIP_VISION}},
        "12": {"class_type": "LoadImage", "inputs": {"image": "keiko_ref.png"}},
        "13": {"class_type": "PrepImageForClipVision", "inputs": {"image": ["12", 0], "interpolation": "LANCZOS", "crop_position": "center", "sharpening": 0.0}},
        "14": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["1", 0], "ipadapter": ["10", 0], "image": ["13", 0], "weight": girl_weight, "weight_type": "linear", "combine_embeds": "concat", "start_at": start_at, "end_at": end_at, "embeds_scaling": "V only", "clip_vision": ["11", 0]}},
        "30": {"class_type": "KSampler", "inputs": {"model": ["14", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0], "seed": seed, "steps": 25, "cfg": 7.0, "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0}},
        "31": {"class_type": "VAEDecode", "inputs": {"samples": ["30", 0], "vae": ["1", 2]}},
        "32": {"class_type": "SaveImage", "inputs": {"images": ["31", 0], "filename_prefix": "c2_rerun"}},
    }
    return wf

# Also generate one WITHOUT IP-Adapter for comparison
def build_no_ipa(prompt, neg, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0], "seed": seed, "steps": 25, "cfg": 7.0, "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "c2_noipa"}},
    }

configs = [
    ("C2_noIPA", None, None, None, 40001),
    ("C2_w010_s03", 0.10, 0.3, 0.9, 40002),
    ("C2_w015_s02", 0.15, 0.2, 0.9, 40003),
    ("C2_w020_s03", 0.20, 0.3, 0.8, 40004),
    ("C2_w035_s00_v2", 0.35, 0.0, 0.8, 40005),
]

print("="*50)
print("C2_EXPOSED Re-run with multiple IP-Adapter weights")
print("="*50)

for name, w, sa, ea, seed in configs:
    print(f"\n[{name}] weight={w}, start_at={sa}, end_at={ea}")
    if w is None:
        wf = build_no_ipa(PROMPT, NEG, seed)
    else:
        wf = build_wf(PROMPT, NEG, w, sa, ea, seed)
    pid = queue(wf)
    print(f"  prompt_id: {pid}")
    o = wait(pid, 300)
    if o:
        fn, sf, tp = get_img(o)
        if fn:
            dl_img(fn, sf, tp, f"{OUT}/{name}.png")
    else:
        print(f"  FAILED")

# Also test with other models on server
OTHER_MODELS = ["animagine_xl_v31.safetensors", "epicrealism_xl.safetensors", "juggernaut_xl_v9.safetensors"]
for model in OTHER_MODELS:
    name = f"C2_{model.split('.')[0]}_noIPA"
    print(f"\n[{name}]")
    wf = build_no_ipa(PROMPT, NEG, 40001)
    wf["1"]["inputs"]["ckpt_name"] = model
    pid = queue(wf)
    print(f"  prompt_id: {pid}")
    o = wait(pid, 300)
    if o:
        fn, sf, tp = get_img(o)
        if fn:
            dl_img(fn, sf, tp, f"{OUT}/{name}.png")
    else:
        print(f"  FAILED")

print(f"\n{'='*50}\nDONE! {OUT}/\n{'='*50}")
