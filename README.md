# AI Video Production

Storyboard-first pipeline for generating realistic AI videos with consistent character identity.

## Pipeline (7 Steps)

| Step | What | Tool | Cost |
|------|------|------|------|
| 0. Storyboard | JSON scene plan (duration, voice, motion) | Manual | Free |
| 1. Assets | Face/fullbody/side per character + voice config | Banana Pro (FAL.ai) | ~$0.10/img |
| 2. Images | One image per scene from storyboard | Banana Pro + epicrealism_xl (ComfyUI) | ~$0.10/img |
| 3. Face Swap | Consistent face identity across all scenes | ReActor (inswapper_128 + GFPGAN v1.4) | Free (GPU) |
| 4. Audio | TTS per scene + SFX mixing | Edge-TTS | Free |
| 5. Video | Static (Ken Burns) / Seedance / Wan2.1 | FFmpeg / ByteDance / ComfyUI | $0–$2/clip |
| 6. Mix | Merge video + audio + SFX per scene | FFmpeg | Free |
| 7. Stitch | Concatenate all scenes → final video | FFmpeg | Free |

## Face Swap (ReActor)

Best pipeline after testing 3 approaches:

| Method | Identity | Eye Color | Speed | Verdict |
|--------|----------|-----------|-------|---------|
| **inswapper_128 + GFPGAN v1.4** | Perfect | Correct | ~5s | **Winner** |
| Pure FaceID Plus v2 | Drifts | Wrong | ~20s | Rejected |
| Hybrid (inswapper → FaceID d0.20) | Good | Correct | ~25s | Not worth it |

## Project Structure

```
benchmark/keiko_production/final/
├── clean/              # Clothed scenes (Banana Pro)
├── stripped/            # Explicit scenes (epicrealism_xl)
├── swapped/            # Face-swapped stripped scenes (ReActor)
├── video/              # Generated video clips
├── flirting_storyboard.json
└── story.md
scripts/
├── produce.py          # Full 15-scene pipeline (assets → QA loop)
└── produce_flirting.py # 20s demo version
```

## Infrastructure

| Service | What | Where |
|---------|------|-------|
| AWS g6e.xlarge (L40S 48GB) | ComfyUI — face swap, strip, image gen | i-07387478d3044b9c7 |
| AWS g6e.2xlarge | Wan2.1 14B video generation | i-0bf53720edb8f40f5 |
| FAL.ai | Banana Pro image generation | API |
| ByteDance Ark | Seedance 1.5 Pro video | API |
| Edge-TTS | Voice generation (free) | Local |
| FFmpeg | Mix + stitch | Local |

## Quick Start

```bash
# Full pipeline
cd scripts
python3 produce.py --step all --comfyui-ip <AWS_IP>

# 20s demo
python3 produce_flirting.py

# Face swap only
python3 ../skills/face-swap/swap.py --batch
```

## Models on AWS

- **epicrealism_xl.safetensors** — best photorealistic SDXL checkpoint
- **inswapper_128.onnx** — face swap model (529MB)
- **buffalo_l** — insightface detection (5 onnx files)
- **GFPGANv1.4.pth** — face restoration
- **IP-Adapter FaceID Plus v2** — tested but rejected (identity drift)
