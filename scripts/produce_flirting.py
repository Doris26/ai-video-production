#!/usr/bin/env python3
"""
Produce a 20s flirting clip following the storyboard-first pipeline.
Step 0: Storyboard (already written)
Step 1: Assets (already have)
Step 2: Generate images
Step 3: Generate audio
Step 4: Generate video (Seedance)
Step 5: Mix per scene
Step 6: Stitch all → final 20s clip
"""
import asyncio, json, os, base64, time, subprocess
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve

# Config
FAL_KEY = open(os.path.expanduser("~/.openclaw/secrets/fal_api_key")).read().strip()
os.environ["FAL_KEY"] = FAL_KEY
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"

OUT = Path("/tmp/flirting_clip")
OUT.mkdir(exist_ok=True)
for d in ["images", "audio", "video", "mixed"]:
    (OUT / d).mkdir(exist_ok=True)

# Load storyboard
with open("/tmp/flirting_storyboard.json") as f:
    STORYBOARD = json.load(f)

# Load face asset
with open("/tmp/banana_assets/girl_1_face.png", "rb") as f:
    GIRL_URL = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

STYLE = "smooth skin texture, clean detailed rendering, consistent bright lighting, same art style as reference image, hyper-realistic, photorealistic, NOT cartoon, NOT anime, 8K"
NEG = "ugly, deformed, cartoon, chibi, Disney, Pixar, blurry, cute, kawaii, Western, blonde, anime, asymmetric eyes, glasses, dark mood, rough texture, grainy"

# Moaning SFX paths
MOANING_SFX = {
    "breathing_soft": "/tmp/moan_hq/gfx_0.mp3",
    "moaning_light": "/tmp/moan_hq/gfx_1.mp3",
    "moaning_medium": "/tmp/moan_hq/gfx_2.mp3",
}

print("=" * 60)
print("  Flirting Clip — 20s Storyboard-Driven Production")
print("=" * 60)

# ════════════════════════════════════════
# Step 2: Generate Images (Banana Pro)
# ════════════════════════════════════════
print("\n--- Step 2: Images ---")
import fal_client

for scene in STORYBOARD:
    sid = scene["scene_id"]
    img_path = OUT / "images" / f"{sid}.png"
    if img_path.exists():
        print(f"  [{sid}] exists, skip")
        continue

    prompt = f"{scene['image_desc']}. {STYLE}"
    print(f"  [{sid}] generating...")

    for attempt in range(3):
        try:
            result = fal_client.submit("fal-ai/nano-banana-pro", arguments={
                "prompt": prompt,
                "negative_prompt": NEG,
                "image_url": GIRL_URL,
                "strength": 0.50,
                "image_size": {"width": 1024, "height": 1024},
                "num_inference_steps": 30,
                "guidance_scale": 7.0,
                "seed": 50000 + hash(sid) % 10000 + attempt,
            }).get()
            urlretrieve(result["images"][0]["url"], str(img_path))
            print(f"    OK")
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"    FAILED: {e}")
    time.sleep(1)

# ════════════════════════════════════════
# Step 3: Generate Audio (Edge-TTS + SFX)
# ════════════════════════════════════════
print("\n--- Step 3: Audio ---")
import edge_tts

async def generate_audio():
    for scene in STORYBOARD:
        sid = scene["scene_id"]
        audio_path = OUT / "audio" / f"{sid}.mp3"
        if audio_path.exists():
            print(f"  [{sid}] exists, skip")
            continue

        vtype = scene["voice_type"]
        text = scene["voice_text"]
        dur = scene["duration"]

        if vtype == "WOMEN_TALKING":
            print(f"  [{sid}] women talking: {text[:20]}...")
            comm = edge_tts.Communicate(text, voice="zh-CN-XiaoyiNeural", rate="-25%", pitch="-5Hz")
            await comm.save(str(audio_path))
        elif vtype == "MOANING":
            print(f"  [{sid}] moaning: {text[:20]}...")
            comm = edge_tts.Communicate(text, voice="zh-CN-XiaoyiNeural", rate="-35%", pitch="-10Hz")
            await comm.save(str(audio_path))
        elif vtype == "NARRATION":
            print(f"  [{sid}] narration: {text[:20]}...")
            comm = edge_tts.Communicate(text, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz")
            await comm.save(str(audio_path))
        elif vtype == "SILENCE":
            # Generate silent audio
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", str(dur), "-c:a", "aac", str(audio_path)], capture_output=True)

        print(f"    OK")

asyncio.run(generate_audio())

# ════════════════════════════════════════
# Step 4: Generate Video (Seedance)
# ════════════════════════════════════════
print("\n--- Step 4: Video (Seedance) ---")

motion_prompts = {
    "flirt_01": "woman leaning forward with shy smile, slight head tilt, hair sway, warm light",
    "flirt_02": "woman sitting on desk, crossing legs, looking down shyly, subtle body movement",
    "flirt_03": "woman at window, turning back over shoulder, hair flowing, sunset light on skin",
    "flirt_04": "close-up face, biting lip, eyes half-closing, slight head movement, warm backlight",
}

# Submit all video tasks
from PIL import Image
import io

video_tasks = {}
for scene in STORYBOARD:
    sid = scene["scene_id"]
    video_path = OUT / "video" / f"{sid}.mp4"
    if video_path.exists():
        print(f"  [{sid}] exists, skip")
        continue

    img_path = OUT / "images" / f"{sid}.png"
    if not img_path.exists():
        print(f"  [{sid}] no image, skip")
        continue

    # Resize for Seedance
    img = Image.open(img_path).resize((720, 720))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    motion = motion_prompts.get(sid, "gentle natural movement")
    body = json.dumps({
        "model": "doubao-seedance-1-5-pro-251215",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": motion}
        ]
    }).encode()

    r = Request(f"{ARK}/contents/generations/tasks", data=body, headers={
        "Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"
    })
    try:
        resp = urlopen(r, timeout=180)
        d = json.loads(resp.read())
        tid = d.get("id", "")
        video_tasks[sid] = tid
        print(f"  [{sid}] submitted: {tid}")
    except Exception as e:
        err = e.read().decode()[:80] if hasattr(e, "read") else str(e)[:80]
        print(f"  [{sid}] FAILED: {err}")
    time.sleep(2)

# Poll all
print(f"\n  Polling {len(video_tasks)} videos...")
remaining = dict(video_tasks)
for poll in range(60):
    if not remaining:
        break
    time.sleep(10)
    for sid, tid in list(remaining.items()):
        try:
            r = Request(f"{ARK}/contents/generations/tasks/{tid}", headers={"Authorization": f"Bearer {ARK_KEY}"})
            d = json.loads(urlopen(r, timeout=30).read())
            if d.get("status") == "succeeded":
                url = d.get("content", {}).get("video_url", "")
                if url:
                    urlretrieve(url, str(OUT / "video" / f"{sid}.mp4"))
                    print(f"    [{sid}] DONE")
                del remaining[sid]
            elif d.get("status") == "failed":
                print(f"    [{sid}] FAILED")
                del remaining[sid]
        except:
            pass

# ════════════════════════════════════════
# Step 5: Mix Per Scene (FFmpeg)
# ════════════════════════════════════════
print("\n--- Step 5: Mix ---")

for scene in STORYBOARD:
    sid = scene["scene_id"]
    video_path = OUT / "video" / f"{sid}.mp4"
    audio_path = OUT / "audio" / f"{sid}.mp3"
    mixed_path = OUT / "mixed" / f"{sid}.mp4"
    sfx_key = scene.get("sfx")

    if mixed_path.exists():
        print(f"  [{sid}] exists, skip")
        continue

    if not video_path.exists() or not audio_path.exists():
        print(f"  [{sid}] missing video or audio, skip")
        continue

    # Get video duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True
    )
    dur = float(result.stdout.strip())

    if sfx_key and sfx_key in MOANING_SFX and os.path.exists(MOANING_SFX[sfx_key]):
        # Mix: mute video audio + voice + SFX
        sfx_path = MOANING_SFX[sfx_key]
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-i", sfx_path,
            "-filter_complex",
            f"[1:a]volume=1.0,atrim=duration={dur}[voice];"
            f"[2:a]aloop=loop=-1:size=2e+09,atrim=duration={dur},volume=0.15[sfx];"
            f"[voice][sfx]amix=inputs=2:duration=first[out]",
            "-map", "0:v", "-map", "[out]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(mixed_path)
        ]
    else:
        # Mix: mute video audio + voice only
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(mixed_path)
        ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  [{sid}] OK")
    else:
        print(f"  [{sid}] ERROR: {r.stderr[-100:]}")

# ════════════════════════════════════════
# Step 6: Stitch All → Final 20s Clip
# ════════════════════════════════════════
print("\n--- Step 6: Stitch ---")

# Create concat list
concat_file = OUT / "concat.txt"
with open(concat_file, "w") as f:
    for scene in STORYBOARD:
        sid = scene["scene_id"]
        mixed_path = OUT / "mixed" / f"{sid}.mp4"
        if mixed_path.exists():
            f.write(f"file '{mixed_path}'\n")

# Stitch
final_path = OUT / "flirting_20s_final.mp4"
cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_file),
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "192k",
    str(final_path)
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode == 0:
    sz = os.path.getsize(str(final_path)) // 1024
    print(f"\n  FINAL VIDEO: {final_path} ({sz}KB)")
else:
    print(f"\n  STITCH ERROR: {r.stderr[-200:]}")

print(f"\n{'=' * 60}")
print(f"  DONE!")
print(f"{'=' * 60}")
