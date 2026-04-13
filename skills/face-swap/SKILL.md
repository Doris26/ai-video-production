---
name: face-swap
description: "Swap Banana Pro face onto AI-generated scenes using ReActor (inswapper_128 + GFPGAN v1.4) via ComfyUI on AWS g6e.xlarge"
---

# Face Swap Pipeline

## Prerequisites
- AWS instance i-07387478d3044b9c7 (g6e.xlarge, L40S 48GB) running
- ComfyUI on port 7860
- ReActor node installed with inswapper_128.onnx + buffalo_l

## Pipeline
1. **Generate target**: epicrealism_xl txt2img (1024x1024, 25 steps, cfg 7.0)
2. **Face swap**: ReActor inswapper_128 (exact identity transfer)
3. **Face restore**: GFPGAN v1.4 (upscale 128px patch)

## Usage

### Quick run (single scene)
```bash
python3 skills/face-swap/swap.py --scene cafe --seed 42
```

### Batch run (all scenes)
```bash
python3 skills/face-swap/swap.py --batch
```

### Custom prompt
```bash
python3 skills/face-swap/swap.py --prompt "woman in red dress, paris street" --seed 100
```

## Models
| Model | Path | Size |
|-------|------|------|
| epicrealism_xl | models/checkpoints/ | SDXL |
| inswapper_128 | models/insightface/ | 529MB |
| buffalo_l | models/insightface/models/ | 5 onnx files |
| GFPGAN v1.4 | models/facerestore_models/ | ~350MB |

## Quality Notes
- inswapper + GFPGAN v1.4 = best identity accuracy (brown eyes, correct features)
- Pure FaceID Plus v2 = wrong eye color, identity drift (not recommended)
- Hybrid (inswapper -> FaceID v2 d20) = marginal improvement, 5x slower (not worth it)
