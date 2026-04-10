#!/usr/bin/env python3
"""v9 - ByteDance Seedream 4.5 + Seedance 1.5 Pro + character consistency"""
import asyncio, json, os, subprocess, time, base64
from pathlib import Path
from urllib.request import urlopen, Request

OUT = Path("/tmp/anime_v9"); OUT.mkdir(parents=True, exist_ok=True)
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK_BASE = "https://ark.cn-beijing.volces.com/api/v3"

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)

def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

def ark_post(endpoint, body):
    """POST to Ark API"""
    import urllib.request
    req = urllib.request.Request(
        f"{ARK_BASE}/{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

def ark_get(url):
    """GET from Ark API"""
    import urllib.request
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {ARK_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

def download(url):
    """Download file from URL"""
    import urllib.request
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()

def gen_image(prompt, idx):
    """Generate image via Seedream 4.5"""
    print(f"  IMG [{idx}] ", end="", flush=True)
    try:
        r = ark_post("images/generations", {
            "model": "doubao-seedream-4-5-251128",
            "prompt": prompt,
            "response_format": "url",
            "size": "1920x1920"
        })
        url = r["data"][0]["url"]
        data = download(url)
        path = OUT / f"img_{idx}.png"
        path.write_bytes(data)
        print(f"OK {len(data)//1024}KB")
        return str(path), url
    except Exception as e:
        print(f"FAIL: {e}")
        return "", ""

def gen_video(image_url, prompt, idx):
    """Generate video via Seedance 1.5 Pro"""
    print(f"  VID [{idx}] ", end="", flush=True)
    try:
        # Submit task
        r = ark_post("contents/generations/tasks", {
            "model": "doubao-seedance-1-5-pro-251215",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt}
            ]
        })
        task_id = r.get("id", "")
        if not task_id:
            print(f"FAIL: no task_id {r}")
            return ""

        # Poll for completion
        for _ in range(120):
            time.sleep(10)
            try:
                status_r = ark_get(f"{ARK_BASE}/contents/generations/tasks/{task_id}")
            except Exception as e:
                continue

            if not isinstance(status_r, dict):
                continue

            status = status_r.get("status", "")
            if status == "succeeded":
                # Get video URL - check multiple response formats
                content = status_r.get("content", status_r.get("output", []))
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "video_url":
                                vid_url = item.get("video_url", {})
                                if isinstance(vid_url, dict):
                                    vid_url = vid_url.get("url", "")
                                if vid_url:
                                    data = download(vid_url)
                                    path = OUT / f"vid_{idx}.mp4"
                                    path.write_bytes(data)
                                    print(f"OK {len(data)//1024//1024}MB")
                                    return str(path)
                            elif "url" in item:
                                vid_url = item["url"]
                                data = download(vid_url)
                                path = OUT / f"vid_{idx}.mp4"
                                path.write_bytes(data)
                                print(f"OK {len(data)//1024//1024}MB")
                                return str(path)
                # Maybe video URL is directly in response
                vid_url = status_r.get("video_url", status_r.get("url", ""))
                if vid_url:
                    data = download(vid_url)
                    path = OUT / f"vid_{idx}.mp4"
                    path.write_bytes(data)
                    print(f"OK {len(data)//1024//1024}MB")
                    return str(path)
                # Debug: print what we got
                print(f"FAIL: no video URL. Keys: {list(status_r.keys())}")
                return ""
            elif status == "failed":
                err = status_r.get("error", {})
                if isinstance(err, dict):
                    print(f"FAIL: {err.get('message', '?')[:60]}")
                else:
                    print(f"FAIL: {err}")
                return ""
        print("TIMEOUT")
        return ""
    except Exception as e:
        print(f"ERR: {e}")
        return ""

print(f"{'='*50}")
print(f"  v9: ByteDance Seedream 4.5 + Seedance 1.5 Pro")
print(f"  {len(NARRS)} scenes")
print(f"{'='*50}")

# STEP 1: Character references
print("\n--- REFERENCES ---")
refs = {}
for name, prompt in [
    ("m", "anime character reference, handsome young man 25 years old, short black hair, warm confident eyes, wearing white casual shirt, half body portrait, clean white background, japanese anime style, masterpiece, best quality, detailed face"),
    ("f", "anime character reference, beautiful mature woman 35 years old, long flowing black hair, fair porcelain skin, gentle elegant eyes, wearing light pink blouse, half body portrait, clean white background, japanese anime style, masterpiece, best quality, detailed face"),
]:
    path, url = gen_image(prompt, f"ref_{name}")
    if path:
        refs[name] = url
    else:
        print(f"  WARNING: {name} reference failed!")

# STEP 2: Scene images
print("\n--- SCENE IMAGES ---")
PROMPTS = [
    "anime man pinning beautiful woman on sofa, passionate kiss, dimly lit living room, romantic atmosphere, warm golden lighting, japanese anime style, masterpiece",
    "anime man gazing lovingly at blushing woman beneath him, her eyes closed panting, intimate warm atmosphere, bedroom, anime style masterpiece",
    "anime man tenderly kissing woman cheek, hands on her shoulders, she trembles with emotion, romantic golden light, anime style",
    "anime man whispering in woman ear intimately, she blushes deeply with closed eyes, warm candle light, anime art masterpiece",
    "anime man carrying beautiful woman in his arms bridal style, walking through hallway to bedroom, passionate romantic, warm lighting, anime",
    "anime couple on bed, man gently pressing woman down, she weakly resists, conflicted expression, warm dim bedroom, anime style",
    "anime passionate kiss on bed, couple embracing tightly, clothes becoming disheveled, romantic atmosphere, anime art masterpiece",
    "anime beautiful woman lying on bed shyly, covering herself with hands, man admiring her beauty, warm candlelight, suggestive anime art",
    "anime man tenderly caressing woman on silk sheets, intimate artistic suggestive scene, warm golden lighting, anime masterpiece",
    "anime woman curled up shyly on bed back turned to man, he gently reaches for her shoulder, emotional warm tones, anime",
    "anime man kissing woman skin tenderly, she runs fingers through his hair, body trembling, intimate artistic anime style",
    "anime couple intertwined passionately on bed, sweating, intense emotional connection, dramatic warm lighting, anime art",
    "anime couple exhausted after passion, lying tangled in sheets, peaceful satisfied expressions, moonlight through window, anime",
    "anime couple sleeping peacefully in warm morning sunlight, tender embrace, beautiful serene atmosphere, anime masterpiece",
    "anime woman with tears in eyes hugging man tightly, emotional morning confession, warm golden sunlight, romantic anime art",
]
VID_PROMPTS = [
    "passionate kiss animation, gentle body movement, warm flickering light",
    "heavy breathing, intimate gazing, bodies close together",
    "tender kiss on cheek, gentle trembling animation, emotional",
    "whispering close, gentle trembling, intimate whisper",
    "carrying motion, walking forward, flowing hair animation",
    "gentle push and pull, conflicted emotions on bed",
    "passionate embrace intensifying, fabric shifting",
    "shy covering movement, gentle hand reaching forward, candlelight",
    "tender caressing motion, trembling response, silk rustling",
    "curling away shyly, gentle touch on bare shoulder",
    "kissing motion along skin, fingers running through hair",
    "passionate intertwined movement, intense dramatic lighting shift",
    "exhausted collapse, heavy breathing, peaceful aftermath",
    "sleeping breathing, sunlight slowly moving across faces",
    "tears forming, tight embrace pulling closer, emotional whisper",
]

img_paths = []
img_urls = []
for i, prompt in enumerate(PROMPTS):
    # Seedream doesn't have /edit endpoint, so we add character description to prompt
    full_prompt = f"{prompt}, featuring a handsome young man with short black hair in white shirt and a beautiful mature woman with long black hair in pink, consistent character appearance"
    path, url = gen_image(full_prompt, i)
    if path:
        img_paths.append(path)
        img_urls.append(url)

print(f"\nImages: {len(img_paths)}/15")

# STEP 3: Videos
print(f"\n--- VIDEOS ({len(img_urls)}) ---")
vid_paths = []
for i, url in enumerate(img_urls):
    path = gen_video(url, VID_PROMPTS[i], i)
    if path:
        vid_paths.append(path)

print(f"\nVideos: {len(vid_paths)}/{len(img_urls)}")

if not vid_paths:
    print("ERROR: No videos generated!")
    exit(1)

# STEP 4: Audio
print(f"\n--- AUDIO ---")
import edge_tts
from pydub import AudioSegment

async def gen_audio():
    combined = AudioSegment.empty()
    narrs = NARRS[:len(vid_paths)]
    for i, text in enumerate(narrs):
        f = str(OUT / f"a{i}.mp3")
        await edge_tts.Communicate(text, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz").save(f)
        combined += AudioSegment.from_mp3(f) + AudioSegment.silent(500)
        print(f"  [{i:02d}] OK")
    path = str(OUT / "narr.mp3")
    combined.export(path, format="mp3", bitrate="128k")
    print(f"  Total: {len(combined)/1000:.1f}s")
    return path

narr = asyncio.run(gen_audio())

# STEP 5: Stitch
print(f"\n--- STITCH ---")
with open(OUT / "c.txt", "w") as f:
    for v in vid_paths:
        f.write(f"file '{v}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(OUT/"c.txt"),
    "-c:v","libx264","-preset","fast","-crf","23","-an",str(OUT/"v.mp4")], capture_output=True)
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,
    "-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0",
    "-shortest",str(OUT/"final_v9.mp4")], capture_output=True)

sz = os.path.getsize(str(OUT/"final_v9.mp4"))
print(f"\n{'='*50}")
print(f"  DONE! final_v9.mp4 ({sz//1024//1024}MB)")
print(f"{'='*50}")
