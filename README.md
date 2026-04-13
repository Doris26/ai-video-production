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

## Face Swap (ReActor via ComfyUI)

**Final pipeline:** ReActor node → inswapper_128 + GFPGAN v1.4

### How It Works
1. **LoadImage** — source face (`assets/girl/girl_1_face.png`)
2. **LoadImage** — target scene image (from Step 2)
3. **ReActorFaceSwap** — swaps face using inswapper_128.onnx (128px face patch)
4. **GFPGAN v1.4** — upscales and restores face quality (visibility 1.0)
5. **SaveImage** — output with consistent character identity

### Settings
| Parameter | Value |
|-----------|-------|
| Swap model | `inswapper_128.onnx` (529MB) |
| Face detection | `retinaface_resnet50` |
| Face restore | `GFPGANv1.4.pth` |
| Face restore visibility | 1.0 |
| CodeFormer weight | 0.5 (unused when GFPGAN selected) |
| Speed | ~5s per image on L40S |
| Instance | i-07387478d3044b9c7 (g6e.xlarge, L40S 48GB) |
| ComfyUI port | 7860 |

### When to Use
- **ALWAYS** after epicrealism strip (face drifts during img2img)
- **OPTIONAL** for Banana Pro scenes (already has face ref, but swap improves consistency)
- **SKIP** for scenes without visible face (back turned, wide shot)

### Models Required on AWS
```
ComfyUI/
├── models/insightface/inswapper_128.onnx          # 529MB swap model
├── models/insightface/models/buffalo_l/            # 5 onnx detection files
│   ├── det_10g.onnx, 1k3d68.onnx, 2d106det.onnx
│   ├── genderage.onnx, w600k_r50.onnx
├── models/facerestore_models/GFPGANv1.4.pth        # face restoration
└── custom_nodes/comfyui-reactor-node/              # ReActor node
```

### Comparison (tested all 3)
| Method | Identity | Eye Color | Speed | Quality | Verdict |
|--------|----------|-----------|-------|---------|---------|
| **inswapper_128 + GFPGAN v1.4** | Perfect | Correct (brown) | ~5s | Good | **Winner** |
| IP-Adapter FaceID Plus v2 | Drifts | Wrong (changed) | ~20s | Best texture | Rejected — wrong identity |
| Hybrid (inswapper → FaceID d0.20) | Good | Correct | ~25s | Slightly smoother | Not worth 5x slower |

### CLI Usage
```bash
# Single scene
python3 skills/face-swap/swap.py --scene cafe --seed 42

# All 4 test scenes
python3 skills/face-swap/swap.py --batch

# Custom prompt
python3 skills/face-swap/swap.py --prompt "woman in red dress, paris" --seed 100

# Different source face
python3 skills/face-swap/swap.py --batch --face custom_face.png
```

### ComfyUI API (Python)
```python
workflow = {
    "10": {"class_type": "LoadImage", "inputs": {"image": "girl_1_face.png"}},
    "12": {"class_type": "LoadImage", "inputs": {"image": "target_scene.png"}},
    "11": {"class_type": "ReActorFaceSwap", "inputs": {
        "enabled": True, "input_image": ["12", 0], "source_image": ["10", 0],
        "swap_model": "inswapper_128.onnx", "facedetection": "retinaface_resnet50",
        "face_restore_model": "GFPGANv1.4.pth", "face_restore_visibility": 1.0,
        "codeformer_weight": 0.5, "detect_gender_input": "no",
        "detect_gender_source": "no", "input_faces_index": "0",
        "source_faces_index": "0", "console_log_level": 1
    }},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "swapped", "images": ["11", 0]}}
}
# POST to http://<AWS_IP>:7860/prompt
```

### Output
- `benchmark/keiko_production/final/swapped/` — 7 face-swapped stripped classroom scenes
- `images/swapped/` — 21 face-swapped images (4 epic + 17 classroom)
- `images/reactor_*.png` — 4 test scene swaps (cafe, beach, sakura, city)

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
