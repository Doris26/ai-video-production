#!/usr/bin/env python3
"""v12 parallel - Submit ALL images at once, then ALL videos at once"""
import asyncio, json, os, subprocess, time, concurrent.futures
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path("/tmp/anime_v12"); OUT.mkdir(parents=True, exist_ok=True)
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)
def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

STYLE = "Chinese 3D animation CG render style like 斗破苍穹, realistic skin texture, soft cinematic lighting, depth of field, high quality Unreal Engine render, 4K detailed"
MALE = "handsome young Chinese man with short black hair, warm confident eyes, wearing casual white shirt"
FEMALE = "beautiful mature Chinese woman with long flowing black hair, fair porcelain skin, gentle alluring eyes, elegant figure, wearing silk nightgown"

SCENE_PROMPTS = [
    f"{STYLE}, {MALE} passionately kissing {FEMALE} on sofa, modern romantic living room, warm golden lighting, intimate close-up",
    f"{STYLE}, close-up of {FEMALE} face blushing deeply with closed eyes, warm dim bedroom atmosphere, romantic tension, cinematic",
    f"{STYLE}, {MALE} tenderly kissing {FEMALE} on the cheek, hands on her shoulders, she trembles with emotion, warm romantic light",
    f"{STYLE}, {MALE} whispering in {FEMALE} ear, intimate close-up, she blushes with eyes closed, warm candle glow, romantic",
    f"{STYLE}, {MALE} carrying {FEMALE} bridal style walking to bedroom, romantic, modern hallway, warm lighting",
    f"{STYLE}, {MALE} and {FEMALE} on bed, he gently holds her, she looks conflicted but yielding, warm dim modern bedroom",
    f"{STYLE}, romantic kiss on silk bed, {MALE} and {FEMALE} embracing, clothes loosened, romantic candlelight, cinematic",
    f"{STYLE}, {FEMALE} on silk bed looking shy, nightgown slipping off shoulder, warm candlelight, modern bedroom, alluring",
    f"{STYLE}, {MALE} tenderly embracing {FEMALE} on silk sheets, intimate artistic scene, warm golden dim lighting, romantic",
    f"{STYLE}, {FEMALE} curled on bed back turned, {MALE} gently reaching for her bare shoulder, emotional warm tones, cinematic",
    f"{STYLE}, {MALE} kissing {FEMALE} shoulder tenderly, she touches his hair, intimate artistic, modern bedroom, warm lighting",
    f"{STYLE}, couple embracing on silk bed, emotional intensity, dramatic warm lighting, cinematic close-up, romantic",
    f"{STYLE}, couple lying together on silk sheets, peaceful satisfied, moonlight through modern curtains, serene",
    f"{STYLE}, couple sleeping peacefully in morning sunlight, tender embrace, modern bedroom, warm beautiful atmosphere",
    f"{STYLE}, {FEMALE} with tears hugging {MALE} tightly, emotional morning, warm golden sunlight, cinematic close-up",
]

VID_PROMPTS = [
    "passionate kiss, gentle body movement, warm flickering light",
    "gentle breathing, blushing deepens, eyes flutter, intimate",
    "tender kiss on cheek, gentle trembling, emotional moment",
    "whispering close, gentle trembling, candle light flickers",
    "carrying motion, walking forward, flowing hair, romantic",
    "gentle embrace on bed, conflicted emotions, yielding",
    "romantic kiss, fabric shifting, intensity building",
    "shy movement, nightgown slipping, candlelight flicker",
    "tender embrace, silk rustling, warm golden glow",
    "gentle turn, hand on bare shoulder, emotional sigh",
    "kissing shoulder, fingers in hair, trembling body",
    "embrace, intense emotion, dramatic light shift",
    "peaceful breathing, settling, moonlight",
    "sleeping breathing, sunlight slowly moving across faces",
    "tears falling, tight embrace, emotional whispered words",
]

def post(endpoint, body):
    r = Request(f"{ARK}/{endpoint}", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def get_json(url):
    r = Request(url, headers={"Authorization": f"Bearer {ARK_KEY}"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def dl(url):
    with urlopen(Request(url), timeout=300) as resp:
        return resp.read()

def gen_img(prompt, idx):
    """Generate single image, with retry on filter"""
    p = OUT / f"img_{idx:02d}.png"
    if p.exists() and p.stat().st_size > 10000:
        print(f"  IMG [{idx:02d}] CACHED")
        # Need URL too - regenerate

    for attempt in range(3):
        try:
            r = post("images/generations", {
                "model": "doubao-seedream-4-5-251128", "prompt": prompt,
                "response_format": "url", "size": "1920x1920"
            })
            url = r["data"][0]["url"]
            d = dl(url)
            p.write_bytes(d)
            print(f"  IMG [{idx:02d}] OK {len(d)//1024}KB")
            return str(p), url
        except Exception as e:
            if "400" in str(e) and attempt == 0:
                prompt = prompt.replace("passionately", "tenderly").replace("passionate", "romantic").replace("alluring", "elegant")
                continue
            if attempt < 2:
                time.sleep(2); continue
            print(f"  IMG [{idx:02d}] FAIL")
            return "", ""
    return "", ""

print(f"{'='*50}")
print(f"  v12 PARALLEL: Donghua CG + Seedance")
print(f"{'='*50}")

# STEP 1: Generate ALL images in parallel (ThreadPool)
print("\n--- IMAGES (parallel) ---")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(gen_img, p, i): i for i, p in enumerate(SCENE_PROMPTS)}
    results = {}
    for f in concurrent.futures.as_completed(futures):
        idx = futures[f]
        results[idx] = f.result()

# Collect successful images
ok_scenes = [(i, results[i][0], results[i][1]) for i in sorted(results) if results[i][0]]
print(f"\nImages: {len(ok_scenes)}/{len(SCENE_PROMPTS)}")

# STEP 2: Submit ALL video tasks at once
print(f"\n--- SUBMIT ALL VIDEOS ({len(ok_scenes)}) ---")
video_tasks = {}
for i, path, img_url in ok_scenes:
    try:
        r = post("contents/generations/tasks", {
            "model": "doubao-seedance-1-5-pro-251215",
            "content": [
                {"type": "image_url", "image_url": {"url": img_url}},
                {"type": "text", "text": VID_PROMPTS[i]}
            ]
        })
        tid = r.get("id", "")
        if tid:
            video_tasks[i] = tid
            print(f"  VID [{i:02d}] submitted: {tid}")
    except Exception as e:
        print(f"  VID [{i:02d}] submit FAIL: {str(e)[:50]}")

print(f"\nSubmitted: {len(video_tasks)} video tasks. Polling...")

# STEP 3: Poll ALL video tasks in parallel
vid_paths = []
remaining = dict(video_tasks)
for poll in range(90):
    if not remaining:
        break
    time.sleep(10)
    done_this_round = []
    for i, tid in list(remaining.items()):
        try:
            sr = get_json(f"{ARK}/contents/generations/tasks/{tid}")
            st = sr.get("status", "")
            if st == "succeeded":
                content = sr.get("content", {})
                vid_url = content.get("video_url", "") if isinstance(content, dict) else ""
                if vid_url:
                    d = dl(vid_url)
                    p = OUT / f"vid_{i:02d}.mp4"; p.write_bytes(d)
                    vid_paths.append(str(p))
                    print(f"  VID [{i:02d}] ✅ {len(d)//1024//1024}MB")
                else:
                    print(f"  VID [{i:02d}] ❌ no url")
                done_this_round.append(i)
            elif st == "failed":
                print(f"  VID [{i:02d}] ❌ failed")
                done_this_round.append(i)
        except:
            pass
    for i in done_this_round:
        del remaining[i]
    if remaining:
        print(f"  ... {len(remaining)} still running", end="\r")

print(f"\nVideos: {len(vid_paths)}/{len(video_tasks)}")

if not vid_paths:
    print("ERROR: No videos!"); exit(1)

# Sort video paths
vid_paths.sort()

# STEP 4: Audio
print(f"\n--- AUDIO ---")
import edge_tts
from pydub import AudioSegment
async def audio():
    c = AudioSegment.empty()
    for i, t in enumerate(NARRS[:len(vid_paths)]):
        f = str(OUT / f"a{i}.mp3")
        await edge_tts.Communicate(t, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz").save(f)
        c += AudioSegment.from_mp3(f) + AudioSegment.silent(500)
        print(f"  [{i:02d}] OK")
    p = str(OUT / "narr.mp3"); c.export(p, format="mp3", bitrate="128k")
    print(f"  Total: {len(c)/1000:.1f}s"); return p
narr = asyncio.run(audio())

# STEP 5: Stitch
print(f"\n--- STITCH ---")
with open(OUT/"c.txt","w") as f:
    for v in vid_paths: f.write(f"file '{v}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(OUT/"c.txt"),"-c:v","libx264","-preset","fast","-crf","23","-an",str(OUT/"v.mp4")],capture_output=True)
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,"-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0","-shortest",str(OUT/"final_v12.mp4")],capture_output=True)
print(f"\n{'='*50}")
print(f"  DONE! {os.path.getsize(str(OUT/'final_v12.mp4'))//1024//1024}MB")
print(f"{'='*50}")
