#!/usr/bin/env python3
"""v8 - Character consistent anime video with your story"""
import asyncio, json, os, subprocess, time, requests
from pathlib import Path
import fal_client

os.environ['FAL_KEY'] = open(os.path.expanduser("~/.openclaw/secrets/fal_api_key")).read().strip()
OUT = Path("/tmp/anime_v8"); OUT.mkdir(parents=True, exist_ok=True)

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)
def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

def upload(data):
    init = requests.post("https://rest.alpha.fal.ai/storage/upload/initiate",
        headers={"Authorization": f"Key {os.environ['FAL_KEY']}", "Content-Type": "application/json"},
        json={"file_name": "i.png", "content_type": "image/png"}).json()
    requests.put(init["upload_url"], data=data, headers={"Content-Type": "image/png"})
    return init["file_url"]

print(f"=== v8: {len(NARRS)} scenes ===")

# STEP 1: References
print("\n--- REFERENCES ---")
refs = {}
for name, p in [
    ("m", "anime character reference, handsome young man 25yo, short black hair, warm eyes, white shirt, half body, clean background, anime style, masterpiece"),
    ("f", "anime character reference, beautiful mature woman 35yo, long black hair, fair skin, gentle eyes, pink blouse, half body, clean background, anime style, masterpiece"),
]:
    h = fal_client.submit("fal-ai/nano-banana-pro", arguments={"prompt": p, "image_size": {"width": 1024, "height": 1024}, "num_images": 1})
    r = fal_client.result("fal-ai/nano-banana-pro", h.request_id)
    d = requests.get(r["images"][0]["url"]).content
    (OUT / f"ref_{name}.png").write_bytes(d)
    refs[name] = upload(d)
    print(f"  {name}: OK {len(d)//1024}KB")

# STEP 2: Scene images with refs
print("\n--- IMAGES ---")
PROMPTS = [
    "anime man pinning woman beneath him, passionate kiss, dimly lit room, romantic",
    "anime man gazing at blushing woman beneath, eyes closed panting, intimate warm",
    "anime man kissing woman cheek, hands on shoulders, she trembles, romantic",
    "anime man whispering in woman ear, she blushes deeply, intimate close-up",
    "anime man carrying woman bridal style to bedroom, passionate warm lighting",
    "anime couple on bed, man pressing woman gently, she resists weakly, conflicted",
    "anime passionate kiss on bed, embracing, clothes disheveled, romantic",
    "anime woman on bed shyly covering herself, man admiring, warm candlelight",
    "anime man caressing woman tenderly, silk sheets, intimate suggestive art",
    "anime woman curled up shyly back turned, man reaching, emotional warm",
    "anime man kissing woman skin, she touches his hair, intimate artistic",
    "anime couple intertwined passionately, sweaty, dramatic warm lighting",
    "anime couple exhausted tangled sheets, peaceful moonlight, aftermath",
    "anime couple sleeping peacefully, morning sunlight, warm embrace tender",
    "anime woman tearful hugging man tight, emotional morning, romantic",
]
VID_PROMPTS = [
    "passionate kiss, gentle movement, warm light", "heavy breathing, gazing, intimate",
    "tender kiss on cheek, trembling", "whispering, gentle trembling",
    "carrying, walking, flowing hair", "gentle push pull, conflicted",
    "passionate embrace, intensity", "shy covering, hand reaching, candlelight",
    "tender caressing, trembling", "curling away, gentle touch",
    "kissing skin, fingers in hair", "passionate intertwining, dramatic",
    "exhausted collapse, breathing", "sleeping, sunlight moving",
    "tears, tight embrace, whisper",
]

ipaths, iurls = [], []
for i, prompt in enumerate(PROMPTS):
    print(f"  [{i:02d}] ", end="", flush=True)
    try:
        h = fal_client.submit("fal-ai/nano-banana-pro/edit", arguments={
            "prompt": f"{prompt}, same characters as reference, anime style, masterpiece",
            "image_urls": [refs["m"], refs["f"]],
            "image_size": {"width": 720, "height": 1280}, "num_images": 1})
        r = fal_client.result("fal-ai/nano-banana-pro/edit", h.request_id)
    except:
        h = fal_client.submit("fal-ai/nano-banana-pro", arguments={
            "prompt": f"{prompt}, anime style, masterpiece",
            "image_size": {"width": 720, "height": 1280}, "num_images": 1})
        r = fal_client.result("fal-ai/nano-banana-pro", h.request_id)
    d = requests.get(r["images"][0]["url"]).content
    p = OUT / f"img_{i:02d}.png"; p.write_bytes(d)
    u = upload(d); ipaths.append(str(p)); iurls.append(u)
    print(f"OK {len(d)//1024}KB")

# STEP 3: Videos
print(f"\n--- VIDEOS ({len(iurls)}) ---")
vpaths = []
for i, u in enumerate(iurls):
    print(f"  [{i:02d}] ", end="", flush=True)
    h = fal_client.submit("fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
        arguments={"prompt": VID_PROMPTS[i], "image_url": u, "duration": "5", "aspect_ratio": "9:16"})
    for _ in range(120):
        time.sleep(10)
        s = str(fal_client.status("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", h.request_id))
        if "Completed" in s: break
        if "Failed" in s: break
    try:
        r = fal_client.result("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", h.request_id)
        vu = r.get("video",{}).get("url","")
        if vu:
            d = requests.get(vu).content
            p = OUT / f"vid_{i:02d}.mp4"; p.write_bytes(d)
            vpaths.append(str(p)); print(f"OK {len(d)//1024//1024}MB")
        else: print("FAIL")
    except: print("ERR")

# STEP 4: Audio
print(f"\n--- AUDIO ---")
import edge_tts
from pydub import AudioSegment
async def audio():
    c = AudioSegment.empty()
    for i, t in enumerate(NARRS[:len(vpaths)]):
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
    for v in vpaths: f.write(f"file '{v}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(OUT/"c.txt"),"-c:v","libx264","-preset","fast","-crf","23","-an",str(OUT/"v.mp4")],capture_output=True)
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,"-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0","-shortest",str(OUT/"final_v8.mp4")],capture_output=True)
print(f"  DONE! {os.path.getsize(str(OUT/'final_v8.mp4'))//1024//1024}MB")
