#!/usr/bin/env python3
"""
Full Anime Video Pipeline v6
Uses fal_client (proven working) for images + video
Edge-TTS for audio, FFmpeg for stitching
"""
import asyncio
import os
import sys
import time
from pathlib import Path

import fal_client
import requests

os.environ['FAL_KEY'] = open(os.path.expanduser("~/.openclaw/secrets/fal_api_key")).read().strip()

OUT = Path("/tmp/anime_v6")
OUT.mkdir(parents=True, exist_ok=True)

SENTENCES = [
    "人世间有一种爱犹如一杯浓香的咖啡令人回味无穷，有一种爱就像醇厚的美酒历久弥香",
    "我的初恋开始于高中时代，应该称之为单恋或叫单相思",
    "那是一个叫琳琳的女孩子，扎着一个马尾巴，相貌清秀，皮肤白皙细嫩",
    "每晚都会在心里默念着她的名字进入梦乡",
    "上课的时候我会默默的注视着她美好的背影，心里甜丝丝的",
    "她和我说的每一句话，我都会牢牢的记住",
    "每次想起她都像吃了一块甜甜的糖果，心中充满甜蜜",
    "由于我过于腼腆的性格，对她的情感一直深藏在心底",
    "毕业后我们各奔前途，再也没有了联系",
    "但是我却从来没有将她忘记，一股柔情涌入心底",
    "大学四年我一直没有交女朋友，那个美好的身影深深印在脑海中",
    "毕业后我成为一名教师，一年后琳琳也回来了",
    "她还是以前的样子，那么清纯，那么美丽",
    "在同学聚会上，我终于鼓起勇气向她表白了",
    "琳琳被我感动了，红晕悄悄布满了她俏丽的脸庞",
]

PROMPTS = [
    "warm coffee shop, golden light, couple silhouettes, romantic atmosphere, anime style, high quality illustration",
    "high school classroom, cherry blossoms outside window, boy looking at girl ahead, anime style",
    "anime girl with ponytail, school uniform, fair skin, beautiful face, close-up portrait, soft lighting",
    "anime boy in bed at night, moonlight, dreamy atmosphere, thinking of someone, gentle expression",
    "classroom scene, boy watching girl from behind, warm sunlight, school setting, anime style",
    "two students talking, boy listening intently, school hallway, warm atmosphere, anime style",
    "boy smiling happily, sweet memory, sparkles, dreamy pink atmosphere, anime style",
    "shy anime boy, unable to confess, sunset school rooftop, melancholic, beautiful sky",
    "graduation scene, two students parting at school gate, cherry blossoms falling, bittersweet, anime",
    "boy alone looking at old photo, nostalgic, soft warm lighting, university dorm, anime style",
    "college campus, boy walking alone, autumn leaves, lonely but determined, anime style",
    "young male teacher, confident smile, classroom, new beginning, anime style, warm colors",
    "beautiful woman reuniting, long black hair, gentle smile, soft lighting, anime style portrait",
    "class reunion, boy confessing to girl, emotional, warm interior, romantic anime scene",
    "anime girl blushing, touched expression, close-up face, romantic, soft pink lighting, beautiful",
]

VIDEO_PROMPTS = [
    "gentle camera movement, warm light flickering, steam rising from coffee cups",
    "cherry blossom petals gently falling past window, students moving slightly",
    "hair gently swaying in breeze, soft breathing animation, eye blink",
    "moonlight shifting across the room, gentle breathing, dreamy atmosphere",
    "sunlight rays moving slowly, girl turns page, boy watches from behind",
    "gentle head movements during conversation, natural body language",
    "sparkles floating around, gentle smile animation, warm glow",
    "wind blowing hair, looking down shyly, sunset clouds moving",
    "cherry blossoms falling continuously, characters walking away slowly, emotional",
    "hand slowly touching photo, soft light flickering, nostalgic atmosphere",
    "leaves falling in wind, walking forward slowly, campus life around",
    "writing on blackboard, confident posture, students in background",
    "hair flowing in wind, gentle smile forming, warm reunion embrace",
    "emotional gestures while speaking, girl's surprised reaction, warm lighting",
    "blushing animation, gentle tears forming, hands touching, romantic moment",
]


def gen_image(prompt, idx):
    print(f"  IMG [{idx:02d}] submitting...")
    handler = fal_client.submit("fal-ai/nano-banana-pro", arguments={
        "prompt": f"{prompt}, masterpiece, best quality, detailed anime illustration",
        "image_size": {"width": 720, "height": 1280},
        "num_images": 1,
    })

    result = fal_client.result("fal-ai/nano-banana-pro", handler.request_id)
    url = result.get("images", [{}])[0].get("url", "")
    if url:
        data = requests.get(url).content
        path = OUT / f"img_{idx:02d}.png"
        path.write_bytes(data)
        print(f"  IMG [{idx:02d}] ✅ {len(data)//1024}KB")
        return str(path), url
    print(f"  IMG [{idx:02d}] ❌")
    return "", ""


def upload_to_fal(image_path):
    fal_key = os.environ['FAL_KEY']
    init = requests.post(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"},
        json={"file_name": "image.png", "content_type": "image/png"}
    ).json()

    with open(image_path, "rb") as f:
        requests.put(init["upload_url"], data=f.read(), headers={"Content-Type": "image/png"})

    return init["file_url"]


def gen_video(image_url, prompt, idx):
    print(f"  VID [{idx:02d}] submitting...")
    handler = fal_client.submit("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", arguments={
        "prompt": prompt,
        "image_url": image_url,
        "duration": "5",
        "aspect_ratio": "9:16",
    })

    # Poll with timeout
    for _ in range(120):
        time.sleep(10)
        status = fal_client.status("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", handler.request_id)
        if hasattr(status, 'status') and status.status == 'COMPLETED':
            break
        if str(status).startswith("Completed"):
            break
        if "Failed" in str(status) or "FAILED" in str(status):
            print(f"  VID [{idx:02d}] ❌ Failed")
            return ""

    result = fal_client.result("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", handler.request_id)
    vid_url = result.get("video", {}).get("url", "")
    if vid_url:
        data = requests.get(vid_url).content
        path = OUT / f"vid_{idx:02d}.mp4"
        path.write_bytes(data)
        print(f"  VID [{idx:02d}] ✅ {len(data)//1024//1024}MB")
        return str(path)
    print(f"  VID [{idx:02d}] ❌")
    return ""


async def gen_audio(sentences):
    import edge_tts
    from pydub import AudioSegment

    print("\n=== AUDIO ===")
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=500)

    for i, text in enumerate(sentences):
        f = str(OUT / f"aud_{i:02d}.mp3")
        comm = edge_tts.Communicate(text, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz")
        await comm.save(f)
        combined += AudioSegment.from_mp3(f) + silence
        print(f"  AUD [{i:02d}] ✅")

    path = str(OUT / "narration.mp3")
    combined.export(path, format="mp3", bitrate="128k")
    print(f"  Total: {len(combined)/1000:.1f}s")
    return path


def stitch(video_files, narration):
    import subprocess
    print("\n=== STITCH ===")

    concat = OUT / "concat.txt"
    with open(concat, "w") as f:
        for v in video_files:
            f.write(f"file '{v}'\n")

    vid_only = str(OUT / "video_only.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-an", vid_only],
                   capture_output=True)

    final = str(OUT / "final_v6.mp4")
    subprocess.run(["ffmpeg", "-y", "-i", vid_only, "-i", narration,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-map", "0:v:0", "-map", "1:a:0", "-shortest", final],
                   capture_output=True)

    print(f"  ✅ {final} ({os.path.getsize(final)//1024//1024}MB)")
    return final


def main():
    N = len(SENTENCES)
    print(f"{'='*50}\n  ANIME VIDEO v6 — {N} scenes\n{'='*50}")

    # Images (parallel-ish via FAL queue)
    print("\n=== IMAGES ===")
    images = []
    for i in range(N):
        path, url = gen_image(PROMPTS[i], i)
        images.append((i, path, url))

    ok_images = [(i, p, u) for i, p, u in images if p]
    print(f"\nImages: {len(ok_images)}/{N}")

    # Upload images to FAL storage for video gen
    print("\n=== UPLOADING IMAGES ===")
    image_urls = {}
    for i, path, _ in ok_images:
        fal_url = upload_to_fal(path)
        image_urls[i] = fal_url
        print(f"  [{i:02d}] uploaded")

    # Videos
    print("\n=== VIDEOS ===")
    videos = []
    for i, path, _ in ok_images:
        vid = gen_video(image_urls[i], VIDEO_PROMPTS[i], i)
        if vid:
            videos.append((i, vid))

    print(f"\nVideos: {len(videos)}/{len(ok_images)}")

    # Audio
    sents = [SENTENCES[i] for i, _ in videos]
    narration = asyncio.run(gen_audio(sents))

    # Stitch
    vid_files = [v for _, v in videos]
    final = stitch(vid_files, narration)

    print(f"\n{'='*50}\n  DONE! {final}\n{'='*50}")


if __name__ == "__main__":
    main()
