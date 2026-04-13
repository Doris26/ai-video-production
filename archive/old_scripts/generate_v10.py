#!/usr/bin/env python3
"""v10 - ByteDance Seedream 4.5 (anime figure 3D) + Seedance 1.5 Pro
Fixed video URL parsing. Anime figurine style matching story scenes."""
import asyncio, json, os, subprocess, time
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path("/tmp/anime_v10"); OUT.mkdir(parents=True, exist_ok=True)
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)
def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

STYLE = "anime figure 3D render style, PVC figurine quality, glossy smooth skin, anime face, subsurface scattering, studio lighting, high detail, 4K"
MALE = "young handsome man with short black hair, confident warm eyes, athletic build, wearing open white shirt"
FEMALE = "beautiful mature woman with long flowing dark hair, fair porcelain skin, gentle alluring eyes, elegant figure"

SCENE_PROMPTS = [
    f"{STYLE}, {MALE} pinning {FEMALE} on sofa, passionate kiss, dimly lit romantic room, warm golden lighting",
    f"{STYLE}, {MALE} gazing down at {FEMALE} beneath him, she blushes with eyes closed, panting, intimate warm atmosphere",
    f"{STYLE}, {MALE} tenderly kissing {FEMALE} on the cheek, hands on her shoulders, she trembles, romantic warm light",
    f"{STYLE}, {MALE} whispering in {FEMALE} ear, she blushes deeply eyes closed, intimate close-up, warm candle glow",
    f"{STYLE}, {MALE} carrying {FEMALE} in his arms bridal style, walking through hallway, passionate romantic",
    f"{STYLE}, couple on bed, {MALE} gently pressing {FEMALE} down, she looks conflicted, warm dim bedroom",
    f"{STYLE}, passionate kiss on bed, {MALE} and {FEMALE} embracing tightly, clothes loosened, romantic atmosphere",
    f"{STYLE}, {FEMALE} on bed looking away shyly, covering herself, {MALE} admiring her, warm candlelight glow",
    f"{STYLE}, {MALE} tenderly touching {FEMALE} on silk bed sheets, intimate artistic scene, warm golden lighting",
    f"{STYLE}, {FEMALE} curled up shyly on bed back turned, {MALE} gently reaching for her shoulder, emotional warm",
    f"{STYLE}, {MALE} kissing {FEMALE} neck tenderly, she runs fingers through his hair, trembling, intimate",
    f"{STYLE}, couple intertwined passionately on bed, sweating, intense emotional, dramatic warm lighting",
    f"{STYLE}, couple lying exhausted tangled in silk sheets, peaceful satisfied, moonlight through window",
    f"{STYLE}, couple sleeping peacefully in warm morning sunlight, tender embrace, serene beautiful",
    f"{STYLE}, {FEMALE} with tears hugging {MALE} tightly, emotional morning scene, warm golden sunlight",
]

VID_PROMPTS = [
    "passionate kiss, gentle body movement, warm flickering light",
    "heavy breathing, intimate gazing, warm atmosphere",
    "tender kiss on cheek, gentle trembling, emotional",
    "whispering close, she trembles, candle light flicker",
    "carrying motion, walking forward, flowing hair",
    "gentle push and pull, conflicted emotions on bed",
    "passionate embrace, fabric shifting, intensity",
    "shy turning away, gentle hand reaching, candlelight",
    "tender caressing, silk rustling, warm glow",
    "curling away, gentle touch on shoulder, emotional",
    "kissing neck, fingers in hair, body trembling",
    "passionate intertwined, intense movement, dramatic",
    "exhausted collapse, heavy breathing, peaceful",
    "sleeping breathing, sunlight slowly moving across",
    "tears forming, tight embrace, emotional whisper",
]

def post(endpoint, body):
    r = Request(f"{ARK}/{endpoint}", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def get(url):
    r = Request(url, headers={"Authorization": f"Bearer {ARK_KEY}"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def dl(url):
    with urlopen(Request(url), timeout=300) as resp:
        return resp.read()

def gen_img(prompt, idx):
    print(f"  IMG [{idx}] ", end="", flush=True)
    try:
        r = post("images/generations", {"model": "doubao-seedream-4-5-251128", "prompt": prompt, "response_format": "url", "size": "1920x1920"})
        url = r["data"][0]["url"]
        d = dl(url)
        p = OUT / f"img_{idx:02d}.png"; p.write_bytes(d)
        print(f"OK {len(d)//1024}KB")
        return str(p), url
    except Exception as e:
        print(f"FAIL: {str(e)[:60]}")
        return "", ""

def gen_vid(image_url, prompt, idx):
    print(f"  VID [{idx:02d}] ", end="", flush=True)
    try:
        r = post("contents/generations/tasks", {
            "model": "doubao-seedance-1-5-pro-251215",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt}
            ]
        })
        tid = r.get("id", "")
        if not tid:
            print(f"FAIL: {r}"); return ""

        for _ in range(90):
            time.sleep(10)
            try:
                sr = get(f"{ARK}/contents/generations/tasks/{tid}")
            except:
                continue
            st = sr.get("status", "")
            if st == "succeeded":
                # content is a DICT with video_url key
                content = sr.get("content", {})
                vid_url = ""
                if isinstance(content, dict):
                    vid_url = content.get("video_url", "")
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "video_url" in item:
                            vid_url = item["video_url"]
                            break
                if vid_url:
                    d = dl(vid_url)
                    p = OUT / f"vid_{idx:02d}.mp4"; p.write_bytes(d)
                    print(f"OK {len(d)//1024//1024}MB")
                    return str(p)
                print(f"FAIL: no URL in content keys={list(sr.keys())}")
                return ""
            elif st == "failed":
                print(f"FAIL"); return ""
        print("TIMEOUT"); return ""
    except Exception as e:
        print(f"ERR: {str(e)[:60]}"); return ""

print(f"{'='*50}\n  v10: Anime Figure 3D + Seedance 1.5 Pro\n  {len(NARRS)} scenes\n{'='*50}")

# IMAGES
print("\n--- IMAGES ---")
imgs, urls = [], []
for i, p in enumerate(SCENE_PROMPTS):
    path, url = gen_img(p, i)
    if path:
        imgs.append(path); urls.append(url)
    else:
        imgs.append(""); urls.append("")
ok = [(i, p, u) for i, (p, u) in enumerate(zip(imgs, urls)) if p]
print(f"\nImages: {len(ok)}/{len(SCENE_PROMPTS)}")

# VIDEOS
print(f"\n--- VIDEOS ---")
vids = []
for i, path, url in ok:
    v = gen_vid(url, VID_PROMPTS[i], i)
    if v: vids.append(v)
print(f"\nVideos: {len(vids)}/{len(ok)}")

if not vids:
    print("ERROR: No videos!"); exit(1)

# AUDIO
print(f"\n--- AUDIO ---")
import edge_tts
from pydub import AudioSegment
async def audio():
    c = AudioSegment.empty()
    for i, t in enumerate(NARRS[:len(vids)]):
        f = str(OUT / f"a{i}.mp3")
        await edge_tts.Communicate(t, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz").save(f)
        c += AudioSegment.from_mp3(f) + AudioSegment.silent(500)
        print(f"  [{i:02d}] OK")
    p = str(OUT / "narr.mp3"); c.export(p, format="mp3", bitrate="128k")
    print(f"  Total: {len(c)/1000:.1f}s"); return p
narr = asyncio.run(audio())

# STITCH
print(f"\n--- STITCH ---")
with open(OUT/"c.txt","w") as f:
    for v in vids: f.write(f"file '{v}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(OUT/"c.txt"),"-c:v","libx264","-preset","fast","-crf","23","-an",str(OUT/"v.mp4")],capture_output=True)
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,"-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0","-shortest",str(OUT/"final_v10.mp4")],capture_output=True)
print(f"\n{'='*50}\n  DONE! {os.path.getsize(str(OUT/'final_v10.mp4'))//1024//1024}MB\n{'='*50}")
