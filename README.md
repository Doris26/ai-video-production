# AI Video Production

Storyboard-first pipeline for generating realistic AI videos with consistent character identity.

## Pipeline (8 Steps)

| Step | What | Tool | Prompt / Config | QA Rules | On Fail |
|------|------|------|-----------------|----------|---------|
| **0. Storyboard** | JSON scene plan | Manual | Each scene: `scene_id`, `duration`, `image_desc`, `voice_type` (NARRATION/WOMEN_TALKING/MOANING/SILENCE), `voice_text`, `voice_character`, `sfx`, `video_type` (STATIC/SEEDANCE/WAN), `motion_prompt`, `explicit` | Total duration matches target; `voice_text` ≤ duration×5 chars; no overlapping voice types; `explicit:true` → `video_type:WAN`; every field filled | Split long narration into sub-scenes (01a, 01b) |
| **1. Assets** | Face/fullbody/side per character + voice + SFX | Banana Pro (FAL.ai) | **Face**: `"Hyper-realistic close-up portrait headshot, {character desc}, plain light gray background, 8K"` (txt2img). **Fullbody**: same prompt, replace "headshot" → "full body head to toe" (img2img from face, strength=0.55). **Side**: replace "headshot" → "three-quarter side angle" (img2img, strength=0.45). **Voice**: Edge-TTS config per char. **SFX**: real audio clips for moaning | Face >50KB, ≥512x512; symmetric eyes; no glasses; correct ethnicity; fullbody+side match face identity; TTS 5s sample sounds correct; SFX plays clean | Regenerate with new seed; if 3x fail → adjust face prompt wording |
| **2. Images** | One image per scene from storyboard `image_desc` | Banana Pro (`fal-ai/nano-banana-pro`) | **Prompt**: `{image_desc}. {STYLE_ANCHOR}` where STYLE_ANCHOR = `"smooth skin texture, clean detailed rendering, consistent bright lighting, same art style as reference image, hyper-realistic, NOT cartoon, NOT anime, 8K"`. **Negative**: `"ugly, deformed, cartoon, chibi, Disney, Pixar, blurry, kawaii, Western, blonde, anime, asymmetric eyes, glasses, dark mood, rough texture, grainy"`. **Params**: face ref image, strength=0.50, steps=30, guidance=7.0, 1024x1024 | R1: Face symmetry; R2: Face pretty; R3: Face matches ref; R4: Style realistic; R5: No glasses; R6: Background matches scene | R1→new seed+"symmetric eyes"; R2→new seed, 3x→lower strength; R3→increase ref weight; R4→add "photorealistic"+fullbody ref; R5→add "no glasses" to neg; R6→strengthen location desc |
| **3a. Strip** | Remove clothing (explicit scenes only) | EpicRealism XL (ComfyUI img2img) | **Prompt**: `"Hyper-realistic, {char_desc}, topless nude, exposed breasts with pink nipples, {location}, NSFW, 8K"`. **Negative**: `"clothes, suit, jacket, blazer, blouse, shirt, bra, skirt, pants, dressed, covered, clothed, fabric"`. **Params**: denoise=0.65 (0.75 for stubborn) | R7: Clothing fully removed; R8: Setting is classroom not bedroom | R7→increase denoise+0.05 (max 0.80)+strengthen strip words; R8→add "classroom,chalkboard"+negate "bedroom,hotel,bed" |
| **3b. Face Swap** | Fix face drift from strip (ONLY for stripped imgs) | ReActor (inswapper_128 + GFPGAN v1.4) via ComfyUI | **Source**: character face asset. **Target**: stripped image. **Config**: `swap_model=inswapper_128.onnx`, `facedetection=retinaface_resnet50`, `face_restore_model=GFPGANv1.4.pth`, `face_restore_visibility=1.0`. Speed: ~5s/image | R1-R3: Face symmetric + pretty + matches ref; no artifacts at blend seams; correct skin tone | Retry swap; if face asset quality low → regenerate asset |
| **4. Audio** | TTS voice + SFX per scene | Edge-TTS (free) + real SFX clips | **Narrator**: `zh-CN-YunxiNeural` rate:-15% pitch:-8Hz. **景子 normal**: `zh-CN-XiaoyiNeural` rate:-10% pitch:+2Hz. **景子 intimate**: `zh-CN-XiaoxiaoNeural` rate:-40% pitch:-12Hz. **黒田**: `zh-CN-YunxiNeural` rate:-5% pitch:-5Hz. **MOANING**: use real SFX from `assets/voice_real/` (TTS moaning sounds robotic) | R13: Correct voice for character; R14: No clipping/static/echo; duration within ±0.5s of scene | R13→verify voice ID; R14→adjust rate/pitch; if TTS too long→trim with `atrim` |
| **5. Video** | Animate images → clips | STATIC (FFmpeg) / SEEDANCE (ByteDance Ark) / WAN (ComfyUI) | **STATIC**: `ffmpeg -loop 1 -i img.png -vf "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1024x1024" -t {dur} out.mp4`. **SEEDANCE**: Ark API, model=`doubao-seedance-1-5-pro`, input=720×720 JPEG, mute original audio. **WAN 2.2**: ComfyUI workflow `UNETLoader(wan2.2_ti2v_5B_fp16)→CLIPVisionEncode→Wan22ImageToVideoLatent+WanImageToVideo→KSampler(25 steps, cfg 5.0, euler)→VAEDecode`, 832×480, 49 frames@24fps, **~28s per clip** on g6e.2xlarge (20GB VRAM, fits easily in 48GB) | R9: Has natural motion; R10: No face morphing/flickering; R11: Face stable throughout; R12: (Seedance) API returned valid video | R9→specific motion prompt; R10→new seed, 3x→simplify motion; R11→less face movement; R12→soften prompt+resize 720x720, or fallback STATIC |
| **6. Mix** | Merge video + audio + SFX per scene | FFmpeg | **Voice only**: `ffmpeg -i video.mp4 -i voice.mp3 -c:v copy -c:a aac -map 0:v -map 1:a -shortest out.mp4`. **Voice+SFX**: `ffmpeg -i video.mp4 -i voice.mp3 -i sfx.mp3 -filter_complex "[1:a]volume=1.0,atrim=duration={dur}[v];[2:a]aloop=loop=-1,atrim=duration={dur},volume=0.15[s];[v][s]amix=inputs=2[out]" -map 0:v -map "[out]" out.mp4`. Layers: voice(1.0) + ambient(-15dB) + SFX(-5dB) | Audio-video in sync; voice audible over SFX; no clipping; duration matches scene | Re-trim audio; adjust SFX volume; re-encode if needed |
| **7. Stitch** | Concat all scenes → final video | FFmpeg | `for f in mixed/*.mp4; do echo "file '$f'" >> concat.txt; done && ffmpeg -f concat -safe 0 -i concat.txt -c:v libx264 -crf 23 -c:a aac final.mp4` | Plays without errors; total duration matches storyboard; no glitches at transitions; audio continuous | Re-encode problem clips; add crossfade if needed |

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

## QA System

QA runs **after EVERY step**, not batch. Flow: `Generate → QA → FAIL → retry (new seed, adjusted params) → QA → max 5x then human review`.

- Uses **Claude API vision** if `ANTHROPIC_API_KEY` set, else file-size heuristics
- Always generates **3 versions**, QA picks best, discards rest
- Seed increments +1 per retry
- All results logged to `qa_log.json`
- Full rules: `scripts/qa_rules.md`

## Project Structure

```
├── README.md
├── skills/
│   └── face-swap/
│       ├── SKILL.md         # Face swap usage guide
│       ├── swap.py          # CLI tool for face swap
│       └── workflow.json    # ComfyUI API workflow
├── scripts/
│   ├── produce.py           # Master producer (full pipeline + QA loop)
│   ├── produce_flirting.py  # 20s demo clip producer
│   ├── generate_seedream.py # Banana Pro image gen
│   ├── generate_comfyui.py  # ComfyUI image gen (EpicRealism)
│   └── qa_rules.md          # 14 QA rules + retry actions
├── assets/
│   ├── keiko/               # Character face/fullbody/side
│   ├── voice_real/          # Real moaning SFX clips
│   ├── voice_test/          # TTS voice samples
│   └── voice_sexy/          # Intimate voice variants
├── benchmark/keiko_production/
│   ├── clean/               # 15 clothed scene images (Banana Pro)
│   └── final/
│       ├── story.md         # Scene script + voice directions
│       ├── flirting_storyboard.json
│       ├── stripped/        # 7 explicit images (EpicRealism)
│       ├── swapped/         # 7 face-swapped images (ReActor)
│       └── video/           # Generated video clips
├── keiko_all_clean_scenes.mp4      # 14 clean Seedance scenes (70s)
├── keiko_swapped_scenes_merged.mp4 # 7 swapped Wan2.1 scenes (21s)
├── wan_scene*.webp                 # Wan2.1 clean scene animations
└── wan_swapped_*.webp              # Wan2.1 swapped scene animations
```

## Infrastructure

| Instance | ID | Type | GPU | RAM | Region | Purpose |
|----------|----|------|-----|-----|--------|---------|
| animatediff-gpu | i-07387478d3044b9c7 | g6e.xlarge | L40S 48GB | 32GB | us-west-2 | Face swap + strip + image gen |
| wan21-2xlarge | i-0307f18835cc4247c | g6e.2xlarge | L40S 48GB | 64GB | us-east-1 | Wan2.1 video (**64GB RAM required**) |
| QWEN3-TTS | i-065bf6a5534ce15b7 | g6e.xlarge | L40S 48GB | 32GB | us-east-1 | Local TTS |

| API | Key Location | Purpose |
|-----|-------------|---------|
| FAL.ai | `~/.openclaw/secrets/fal_api_key` | Banana Pro (via `fal_client` SDK) |
| ByteDance Ark | `~/.openclaw/secrets/bytedance_ark_api_key` | Seedance video |
| Anthropic | `ANTHROPIC_API_KEY` env | Claude Vision QA |
| Edge-TTS | **No key** (free) | Voice generation |

**GPU Quota:** 96 vCPUs P-instances approved in us-east-1, us-east-2, us-west-2.

**SSH:** `ssh -i ~/.ssh/sd-gpu-key.pem ubuntu@<IP>`

## Quick Start

```bash
# Full pipeline
python3 scripts/produce.py --step all --comfyui-ip <AWS_IP>

# 20s demo
python3 scripts/produce_flirting.py

# Face swap only
python3 skills/face-swap/swap.py --batch

# Start GPU instances
aws ec2 start-instances --instance-ids i-07387478d3044b9c7 --region us-west-2  # image work
aws ec2 start-instances --instance-ids i-0307f18835cc4247c --region us-east-1  # Wan2.1 video
```

## All Models on AWS

| Model | File | Size | Instance | Purpose |
|-------|------|------|----------|---------|
| EpicRealism XL | `epicrealism_xl.safetensors` | SDXL | animatediff-gpu | Strip img2img |
| inswapper_128 | `inswapper_128.onnx` | 529MB | animatediff-gpu | Face swap |
| buffalo_l | `buffalo_l/*.onnx` | 5 files | animatediff-gpu | Face detection |
| GFPGAN v1.4 | `GFPGANv1.4.pth` | ~350MB | animatediff-gpu | Face restoration |
| Wan2.2 TI2V-5B | `wan2.2_ti2v_5B_fp16.safetensors` | 9.4GB | wan21-2xlarge | Video gen (5B params, fp16) |
| UMT5-XXL fp8 | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.3GB | wan21-2xlarge | Text encoder |
| CLIP Vision H | `clip_vision_h.safetensors` | 1.2GB | wan21-2xlarge | Image encoder |
| Wan 2.2 VAE | `wan2.2_vae.safetensors` | 1.4GB | wan21-2xlarge | Video decoder (16×16×4 compression) |

## Key Learnings

- **Storyboard first** — never generate images/video without structured storyboard
- **Face swap ONLY for stripped images** — clean Banana Pro images already have correct face
- **inswapper_128 + GFPGAN > IP-Adapter FaceID** — better identity, correct eye color
- **Wan 2.2 TI2V-5B replaces Wan 2.1 14B** — 12x faster (28s vs 5min), 9.4GB vs 16GB, no fp8 garbage, fits on any 48GB GPU
- **Banana Pro glasses bug** — always include "glasses" in negative prompt
- **Style anchor in EVERY prompt** — prevents cartoon/anime drift
- **Voice: never overlap** narration and dialogue in same scene
- **Xiaoxiao for sexy, Xiaoyi for scared** — different Edge-TTS voices for different emotions
- **Real SFX > TTS moaning** — TTS can't sound natural for intimate scenes
- **Seedance filters NSFW** — use WAN for explicit, STATIC (Ken Burns) as free fallback
- **torch 2.6 + CUDA 12.4** tested working for Wan 2.2
- **Wan 2.2 models** from [Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)
