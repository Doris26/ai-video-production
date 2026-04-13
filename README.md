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

## Detailed Pipeline Flow

```
Step 0: STORYBOARD (JSON — source of truth)
    ▼   QA: duration fits, voice_text ≤ duration×5 chars, no overlapping voices
Step 1: ASSETS (characters + scenes + props + voice + SFX)
    ▼   QA: face symmetric, no glasses, identity consistent across angles
Step 2: IMAGES (Banana Pro with face ref + style anchor)
    ▼   QA: Rules 1-6 (face, style, background) — auto-retry ≤5x
Step 3: STRIP + FACE SWAP (explicit scenes only)
    ▼   QA: Rules 7-8 (clothing removed, classroom kept) + Rules 1-3 (face)
Step 4: AUDIO (Edge-TTS per character + real SFX)
    ▼   QA: Rules 13-14 (correct voice, no artifacts)
Step 5: VIDEO (STATIC / SEEDANCE / WAN per scene)
    ▼   QA: Rules 9-12 (motion, artifacts, face stable, filter)
Step 6: MIX (video + voice + ambient + SFX → per scene)
    ▼   QA: sync, volume, no clipping
Step 7: STITCH (concat all → final video)
    ▼   QA: plays ok, total duration, no transition glitches
```

### Storyboard Format (Step 0)

```json
{
  "scene_id": "01a",
  "duration": 5,
  "image_desc": "Woman walking through school gate, cherry blossoms",
  "voice_type": "NARRATION | WOMEN_TALKING | MOANING | SILENCE",
  "voice_text": "景子到任后立即成为学生的偶像。",
  "voice_character": "narrator | keiko | kuroda",
  "sfx": "morning_ambient | moaning_light | null",
  "video_type": "STATIC | SEEDANCE | WAN",
  "motion_prompt": "subtle head turn, gentle smile",
  "explicit": false
}
```

Rules:
- `voice_text` fits duration (5s ≈ 25 Chinese chars)
- Long narration → split into sub-scenes (01a, 01b, 01c)
- Voice: EITHER narration OR dialogue — **NEVER overlapping**
- `explicit: true` → `video_type: WAN` (Seedance filters NSFW)
- `STATIC` = Ken Burns zoom/pan (free, no API)

### Asset Categories (Step 1)

| Category | What | Example |
|----------|------|---------|
| **Characters (角色)** | Face + fullbody + side per character | `keiko_face.png`, `keiko_fullbody.png` |
| **Scenes (场景)** | Location backgrounds | Classroom, hallway, school gate |
| **Props (道具)** | Consistent objects across scenes | Textbook, briefcase, chalk, coffee cup |
| **Voice** | Edge-TTS config per character | `zh-CN-XiaoyiNeural` rate:-10% pitch:+2Hz |
| **SFX** | Real audio clips for intimate scenes | `assets/voice_real/gfx_0.mp3` |

Character asset flow: Face (txt2img) → Fullbody (img2img strength=0.55) → Side (img2img strength=0.45)

### Image Generation (Step 2)

**Style Anchor** (EVERY prompt):
```
smooth skin texture, clean detailed rendering, consistent bright lighting,
same art style as reference image, hyper-realistic, NOT cartoon, NOT anime, 8K
```

**Global Negative** (ALWAYS):
```
ugly, deformed, cartoon, chibi, Disney, Pixar, blurry, cute, kawaii,
Western, blonde, anime, asymmetric eyes, glasses, dark mood, rough texture, grainy
```

Banana Pro params: strength=0.50, steps=30, guidance=7.0, 1024x1024

### Video Types (Step 5)

| Type | When | How | Cost |
|------|------|-----|------|
| **STATIC** | Narration, close-ups | Ken Burns zoom/pan (FFmpeg) | Free |
| **SEEDANCE** | Clean motion scenes | ByteDance Ark API (`doubao-seedance-1-5-pro`) | ~$0.01 |
| **WAN** | Explicit motion scenes | ComfyUI on g6e.2xlarge (L40S, **64GB RAM required**) | ~$0.15 |

Ken Burns: `ffmpeg -loop 1 -i img.png -vf "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1024x1024" -t 5 out.mp4`

Wan2.1: UNETLoader → CLIPVisionEncode → WanImageToVideo[0,1,2] → KSampler(25 steps) → VAEDecode

### Audio Pipeline (Step 4 + Step 6)

**3-layer mixing per scene:**

| Layer | Source | Volume |
|-------|--------|--------|
| Voice | Edge-TTS (per character) | Full (1.0) |
| Ambient | Seedance original or silent | -15dB (0.15) |
| SFX | Real moaning clips | -5dB (0.3) |

**Voice mapping:**

| Character | Voice ID | Rate | Pitch | For |
|-----------|----------|------|-------|-----|
| Narrator | zh-CN-YunxiNeural | -15% | -8Hz | Scene descriptions |
| 景子 (normal) | zh-CN-XiaoyiNeural | -10% | +2Hz | Dialogue |
| 景子 (intimate) | zh-CN-XiaoxiaoNeural | -40% | -12Hz | Breathy/moaning |
| 黒田 | zh-CN-YunxiNeural | -5% | -5Hz | Male dialogue |

Xiaoxiao = mature/deep → intimate scenes. Xiaoyi = younger → scared/pleading. Real SFX clips preferred over TTS for moaning.

## QA Rules (14 total — `scripts/qa_rules.md`)

QA runs **after EVERY step**, not batch. Flow: Generate → QA → FAIL → retry (new seed) → QA → max 5x.

Uses Claude API vision if `ANTHROPIC_API_KEY` set, else file-size heuristics. Generates 3 versions, picks best.

### Image QA (8 rules)

| # | Rule | On Fail |
|---|------|---------|
| 1 | Face Symmetry | New seed + "beautiful symmetric eyes" |
| 2 | Face Pretty | New seed; 3x → lower strength -0.05 |
| 3 | Face Consistent | Increase IP-Adapter weight +0.1 |
| 4 | Style Realistic | Add "photorealistic" + fullbody ref |
| 5 | No Glasses | Add to prompt + negative |
| 6 | Background Correct | Strengthen location in prompt |
| 7 | Clothing Stripped | Increase denoise +0.05 (max 0.80) |
| 8 | Not Bedroom | Add "classroom, chalkboard" + negate "bedroom" |

### Video QA (4 rules)

| # | Rule | On Fail |
|---|------|---------|
| 9 | Has Motion | More specific motion prompt |
| 10 | No Artifacts | New seed; 3x → simplify motion |
| 11 | Face Stable | Simpler motion, increase face weight |
| 12 | Content Filter | Soften prompt, resize to 720x720, or STATIC fallback |

### Audio QA (2 rules)

| # | Rule | On Fail |
|---|------|---------|
| 13 | Voice Correct | Verify voice ID for character |
| 14 | Audio Quality | Adjust rate/pitch |

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
| Wan2.1 I2V 14B fp8 | `wan2.1_i2v_480p_14B_fp8_e4m3fn.safetensors` | 16GB | wan21-2xlarge | Video gen |
| UMT5-XXL | `umt5_xxl_fp16.safetensors` | 11GB | wan21-2xlarge | Text encoder |
| CLIP Vision H | `clip_vision_h.safetensors` | 1.2GB | wan21-2xlarge | Image encoder |
| Wan 2.1 VAE | `wan_2.1_vae.safetensors` | 243MB | wan21-2xlarge | Video decoder |

## Key Learnings

- **Storyboard first** — never generate images/video without structured storyboard
- **Face swap ONLY for stripped images** — clean Banana Pro images already have correct face
- **inswapper_128 + GFPGAN > IP-Adapter FaceID** — better identity, correct eye color
- **Wan2.1 needs 64GB RAM** — g6e.xlarge (32GB) produces garbage
- **Banana Pro glasses bug** — always include "glasses" in negative prompt
- **Style anchor in EVERY prompt** — prevents cartoon/anime drift
- **Voice: never overlap** narration and dialogue in same scene
- **Xiaoxiao for sexy, Xiaoyi for scared** — different Edge-TTS voices for different emotions
- **Real SFX > TTS moaning** — TTS can't sound natural for intimate scenes
- **Seedance filters NSFW** — use WAN for explicit, STATIC (Ken Burns) as free fallback
- **torch 2.6 + CUDA 12.4** tested working for Wan2.1
