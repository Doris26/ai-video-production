#!/usr/bin/env python3
"""Face swap pipeline: epicrealism_xl + ReActor (inswapper_128 + GFPGAN v1.4) via ComfyUI API."""

import argparse
import json
import time
import urllib.request
import os

COMFYUI_URL = "http://127.0.0.1:7860"
SOURCE_FACE = "girl_1_face.png"
CHECKPOINT = "epicrealism_xl.safetensors"
SWAP_MODEL = "inswapper_128.onnx"
RESTORE_MODEL = "GFPGANv1.4.pth"

SCENES = {
    "cafe": {"seed": 42, "prompt": "beautiful young woman, portrait, cafe background, natural lighting, photorealistic, 8k"},
    "beach": {"seed": 123, "prompt": "beautiful young woman walking on tropical beach, sunset golden hour, ocean waves, photorealistic, 8k"},
    "sakura": {"seed": 456, "prompt": "beautiful young woman standing under cherry blossom trees, spring, soft pink petals falling, photorealistic, 8k"},
    "city": {"seed": 789, "prompt": "beautiful young woman in neon-lit city street at night, cyberpunk atmosphere, rain reflections, photorealistic, 8k"},
}

NEGATIVE = "ugly, deformed, blurry, low quality, cartoon, anime"


def build_workflow(prompt_text, seed, prefix, source_face=SOURCE_FACE):
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt_text, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["4", 1]}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed, "steps": 25, "cfg": 7.0,
                "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
                "model": ["4", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "10": {
            "class_type": "LoadImage",
            "inputs": {"image": source_face}
        },
        "11": {
            "class_type": "ReActorFaceSwap",
            "inputs": {
                "enabled": True,
                "input_image": ["8", 0],
                "source_image": ["10", 0],
                "swap_model": SWAP_MODEL,
                "facedetection": "retinaface_resnet50",
                "face_restore_model": RESTORE_MODEL,
                "face_restore_visibility": 1.0,
                "codeformer_weight": 0.5,
                "detect_gender_input": "no",
                "detect_gender_source": "no",
                "input_faces_index": "0",
                "source_faces_index": "0",
                "console_log_level": 1
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["11", 0]}
        }
    }


def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt", data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def wait_for_completion(prompt_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
        resp = urllib.request.urlopen(req)
        history = json.loads(resp.read())
        if prompt_id in history:
            status = history[prompt_id]["status"]
            if status.get("completed"):
                return status["status_str"]
        time.sleep(2)
    return "timeout"


def run_scene(name, prompt_text, seed, source_face=SOURCE_FACE):
    prefix = f"reactor_{name}"
    workflow = build_workflow(prompt_text, seed, prefix, source_face)
    result = queue_prompt(workflow)
    prompt_id = result["prompt_id"]
    errors = result.get("node_errors", {})
    if errors:
        print(f"  [{name}] errors: {errors}")
        return None
    print(f"  [{name}] queued: {prompt_id}")
    status = wait_for_completion(prompt_id)
    print(f"  [{name}] {status}")
    return prompt_id


def main():
    parser = argparse.ArgumentParser(description="Face swap via ReActor + ComfyUI")
    parser.add_argument("--scene", choices=list(SCENES.keys()), help="Run a single scene")
    parser.add_argument("--batch", action="store_true", help="Run all scenes")
    parser.add_argument("--prompt", type=str, help="Custom prompt text")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--face", type=str, default=SOURCE_FACE, help="Source face image filename (must be in ComfyUI/input/)")
    parser.add_argument("--prefix", type=str, default="reactor_custom", help="Output filename prefix")
    args = parser.parse_args()

    if args.batch:
        print("Running all scenes...")
        for name, cfg in SCENES.items():
            run_scene(name, cfg["prompt"], cfg["seed"], args.face)
        print("Done.")
    elif args.scene:
        cfg = SCENES[args.scene]
        print(f"Running {args.scene}...")
        run_scene(args.scene, cfg["prompt"], cfg["seed"], args.face)
    elif args.prompt:
        print(f"Running custom prompt (seed={args.seed})...")
        run_scene(args.prefix, args.prompt, args.seed, args.face)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
