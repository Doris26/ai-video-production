#!/usr/bin/env python3
"""Final 8 scenes with new 3D建模脸 reference face, masked dual IP-Adapter for couples."""
import json, time, urllib.request, urllib.parse, uuid, os

COMFYUI = "http://127.0.0.1:7860"
CID = str(uuid.uuid4())
CKPT = "xxmix_sdxl.safetensors"
IPA_MODEL = "ip-adapter-plus_sdxl_vit-h.safetensors"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
OUT = "/tmp/keiko_final"
os.makedirs(OUT, exist_ok=True)

CLASSROOM = "Japanese high school classroom, rows of wooden desks and chairs, green chalkboard at front wall, raised wooden teaching platform, tall windows on left wall with white curtains and warm afternoon sunlight, cream-colored walls, fluorescent ceiling lights, polished wooden floor"
NEG_CLEAN = "ugly, deformed, bad anatomy, bad hands, missing fingers, extra fingers, blurry, low quality, watermark, text, logo, gray background, studio background, plain background"
NEG_COUPLE = NEG_CLEAN + ", solo, single person, two girls, 2girls"
NEG_NSFW = NEG_CLEAN + ", suit, jacket, blazer, formal wear, business suit, pencil skirt, blouse, fully clothed"
NEG_DISH = NEG_COUPLE + ", neat clothes, pristine, tidy"

SCENES = {
    "A1_TEACHING": {
        "prompt": f"1girl, medium shot, beautiful Japanese female teacher aged 24 standing on raised wooden teaching platform, holding open textbook, wearing gray suit jacket over white blouse, pencil skirt, black heels, long black hair with wispy bangs, confident smile, 3D CG anime style, semi-realistic face, high detail, cinematic. {CLASSROOM}",
        "neg": NEG_CLEAN, "type": "solo", "seed": 80001,
    },
    "A2_TEACHING_CLOSEUP": {
        "prompt": f"1girl, close-up portrait, beautiful Japanese female teacher aged 24 at classroom podium, holding chalk, writing on green chalkboard, wearing gray suit, white blouse, long black hair with wispy bangs over forehead, warm smile, big sparkling dark brown eyes, afternoon light from windows on her face, 3D CG anime style, semi-realistic face, high detail. {CLASSROOM}",
        "neg": NEG_CLEAN, "type": "solo", "seed": 80002,
    },
    "B1_CONFRONTATION": {
        "prompt": f"2people, 1boy 1girl, medium shot, on the left a beautiful Japanese female teacher aged 24 with long black hair and wispy bangs wearing gray suit with arms crossed looking stern, on the right a tall Japanese male student aged 18 with short spiky black hair wearing dark navy school uniform gakuran looking defiant with hands in pockets, standing face to face between rows of wooden desks, tense confrontation, afternoon light, 3D CG anime style, semi-realistic face, high detail, cinematic. {CLASSROOM}",
        "neg": NEG_COUPLE, "type": "couple", "seed": 80003,
    },
    "B2_CONFRONTATION_WIDE": {
        "prompt": f"2people, 1boy 1girl, wide shot, on the left a beautiful Japanese female teacher aged 24 with long black hair and wispy bangs wearing gray suit standing on teaching platform pointing angrily, on the right a tall Japanese male student aged 18 with short spiky black hair wearing dark navy school uniform sitting at desk smirking, dramatic afternoon light from tall windows, 3D CG anime style, semi-realistic face, cinematic. {CLASSROOM}",
        "neg": NEG_COUPLE, "type": "couple", "seed": 80004,
    },
    "C1_VULNERABLE": {
        "prompt": f"1girl, medium shot, beautiful Japanese woman aged 24 sitting on wooden teaching platform in classroom, wearing only unbuttoned white blouse open showing cleavage and black lace bra, no skirt, legs drawn up, arms hugging knees, long black hair with wispy bangs falling over face, crying with tears on cheeks, vulnerable expression, big sparkling eyes filled with tears, afternoon light from windows, 3D CG anime style, semi-realistic face, emotional, high detail. {CLASSROOM}",
        "neg": NEG_CLEAN + ", suit jacket, blazer, neat, tidy", "type": "solo", "seed": 80005,
    },
    "C2_EXPOSED": {
        "prompt": f"1girl, full body shot, beautiful Japanese woman aged 24 standing on raised wooden teaching platform, topless, exposed large breasts with pink nipples, wearing only black sheer panties and black high heels, arms raised behind head with hands on neck, legs spread apart wider than shoulders, flushed face looking down in shame, long black hair with wispy bangs flowing down back, warm afternoon sunlight from windows, sweat glistening on skin, 3D CG anime style, semi-realistic face, NSFW, high detail, masterpiece. {CLASSROOM}, male students sitting on floor around platform",
        "neg": NEG_NSFW, "type": "solo", "seed": 80006,
    },
    "D1_AFTERMATH": {
        "prompt": f"2people, 1boy 1girl, medium shot, on the left a beautiful Japanese woman aged 24 with long disheveled black hair and wispy bangs lying on wooden classroom floor exhausted wearing torn open white blouse showing skin, tears and sweat on face, expression of exhaustion, on the right a tall Japanese male student aged 18 with short spiky black hair in dark navy school uniform standing with arms crossed cold expression looking down, nighttime harsh fluorescent lighting, 3D CG anime style, semi-realistic face, emotional, cinematic. {CLASSROOM}, windows showing dark night outside",
        "neg": NEG_DISH, "type": "couple", "seed": 80007,
    },
    "E1_EMOTION": {
        "prompt": f"1girl, close-up emotional portrait, beautiful Japanese woman aged 24 with tears streaming down porcelain cheeks, big sparkling dark brown eyes filled with tears, wispy bangs stuck to forehead with sweat, biting lower lip, expression of anguish, wearing torn white blouse showing collarbone and shoulder, long disheveled black hair partially covering face, warm golden light from classroom window behind her, 3D CG anime style, semi-realistic face, highly detailed, emotional, cinematic. Blurred Japanese high school classroom background with green chalkboard and wooden desks visible",
        "neg": NEG_CLEAN + ", neat, tidy, happy, smiling", "type": "solo", "seed": 80008,
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
                    print(f"  ERROR: {json.dumps(st)[:200]}")
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

def build_solo(prompt, neg, seed, gw=0.5):
    """Solo girl scene with IP-Adapter (no mask needed)."""
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
        "32": {"class_type": "SaveImage", "inputs": {"images": ["31", 0], "filename_prefix": "final"}},
    }

def build_couple(prompt, neg, seed, gw=0.5, bw=0.4):
    """Couple scene with masked IP-Adapter: girl left, boy right."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "10": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": IPA_MODEL}},
        "11": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": CLIP_VISION}},
        # Girl ref + left mask
        "20": {"class_type": "LoadImage", "inputs": {"image": "keiko_ref.png"}},
        "21": {"class_type": "PrepImageForClipVision", "inputs": {"image": ["20", 0], "interpolation": "LANCZOS", "crop_position": "center", "sharpening": 0.0}},
        "22": {"class_type": "LoadImage", "inputs": {"image": "mask_left.png"}},
        "25": {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["1", 0], "ipadapter": ["10", 0], "image": ["21", 0],
            "weight": gw, "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 0.8, "embeds_scaling": "V only",
            "clip_vision": ["11", 0], "attn_mask": ["22", 1],
        }},
        # Boy ref + right mask
        "30": {"class_type": "LoadImage", "inputs": {"image": "kuroda_ref.png"}},
        "31": {"class_type": "PrepImageForClipVision", "inputs": {"image": ["30", 0], "interpolation": "LANCZOS", "crop_position": "center", "sharpening": 0.0}},
        "32": {"class_type": "LoadImage", "inputs": {"image": "mask_right.png"}},
        "35": {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["25", 0], "ipadapter": ["10", 0], "image": ["31", 0],
            "weight": bw, "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 0.8, "embeds_scaling": "V only",
            "clip_vision": ["11", 0], "attn_mask": ["32", 1],
        }},
        "50": {"class_type": "KSampler", "inputs": {
            "model": ["35", 0], "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0
        }},
        "51": {"class_type": "VAEDecode", "inputs": {"samples": ["50", 0], "vae": ["1", 2]}},
        "52": {"class_type": "SaveImage", "inputs": {"images": ["51", 0], "filename_prefix": "final_couple"}},
    }

print("="*50)
print("FINAL 8 Scenes — new 3D建模脸 face + masked couples")
print("="*50)

for name, cfg in SCENES.items():
    print(f"\n[{name}] type={cfg['type']}")
    if cfg["type"] == "solo":
        wf = build_solo(cfg["prompt"], cfg["neg"], cfg["seed"], gw=0.5)
    else:
        wf = build_couple(cfg["prompt"], cfg["neg"], cfg["seed"], gw=0.5, bw=0.4)
    pid = queue(wf)
    print(f"  prompt_id: {pid}")
    o = wait(pid, 300)
    if o:
        fn, sf, tp = get_img(o)
        if fn: dl_img(fn, sf, tp, f"{OUT}/{name}.png")
    else:
        print(f"  FAILED")

print(f"\n{'='*50}\nDONE!\n{'='*50}")
