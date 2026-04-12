# QA Rules — Clear Pass/Fail Criteria + Retry Actions

## Image QA (runs after EVERY image generation)

### Rule 1: Face Symmetry
- **Check**: Are both eyes same size, aligned, looking same direction?
- **FAIL if**: cross-eyed, one eye bigger, eyes at different heights, wonky pupil
- **Retry action**: regenerate with same prompt + new seed + add "beautiful symmetric eyes, perfect face" to prompt

### Rule 2: Face Pretty
- **Check**: Is the face attractive, well-rendered, no artifacts?
- **FAIL if**: ugly, deformed, melted features, uncanny valley, skin blotches
- **Retry action**: regenerate with new seed. If fails 3x, lower img2img strength by 0.05

### Rule 3: Face Consistent
- **Check**: Does this face look like the same person as the asset reference?
- **FAIL if**: completely different person, different ethnicity, different age
- **Retry action**: increase IP-Adapter weight by 0.1 (for ComfyUI) or lower Banana strength by 0.05

### Rule 4: Style Realistic
- **Check**: Is the style photorealistic / hyper-realistic?
- **FAIL if**: cartoon, Disney/Pixar, anime, chibi, 2D flat
- **Retry action**: add "photorealistic photograph style, NOT cartoon, NOT anime" to prompt + use fullbody asset as ref instead of face

### Rule 5: No Glasses
- **Check**: Is the person NOT wearing glasses?
- **FAIL if**: wearing any glasses, sunglasses, spectacles, reading glasses
- **Retry action**: add "no glasses, no spectacles" to prompt + add "glasses, spectacles" to negative

### Rule 6: Background Correct
- **Check**: Does background match the scene description (classroom/hallway/outside)?
- **FAIL if**: wrong location (bedroom when should be classroom), no background (gray/white studio)
- **Retry action**: strengthen background description in prompt + add wrong background to negative

### Rule 7: Clothing Stripped (NSFW scenes only)
- **Check**: Is upper body exposed with visible nipples?
- **FAIL if**: still wearing shirt/blouse/bra/jacket, only cleavage without nipples
- **Retry action**: increase denoise by 0.05 (max 0.80) + strengthen "topless, nude, exposed breasts, nipples" in prompt + add ALL clothing words to negative

### Rule 8: Not Bedroom (stripped scenes only)
- **Check**: Is the setting a classroom, NOT a bedroom/hotel?
- **FAIL if**: bedroom furniture, hotel room, bed visible
- **Retry action**: add "Japanese classroom, chalkboard, desks" to prompt + add "bedroom, hotel, bed" to negative

## Video QA (runs after EVERY video generation)

### Rule 9: Has Motion
- **Check**: Does the video show natural movement?
- **FAIL if**: completely frozen/static, only camera movement
- **Retry action**: make motion prompt more specific ("turn head left, blink, hand gesture")

### Rule 10: No Artifacts
- **Check**: Is video free of visual glitches?
- **FAIL if**: face morphing, body parts distorting, flickering, color glitches
- **Retry action**: regenerate with new seed. If fails 3x, simplify motion prompt

### Rule 11: Face Stable
- **Check**: Does face stay recognizable throughout?
- **FAIL if**: face changes identity mid-video, face melts/distorts
- **Retry action**: use simpler motion (less face movement), increase face weight

### Rule 12: Content Filter (Seedance only)
- **Check**: Did the API return a valid video (not rejected)?
- **FAIL if**: API returns error, timeout, or empty response
- **Retry action**: soften prompt (remove "tears", "frightened", etc.), reduce image size to 720x720 JPEG

## Audio QA (runs after EVERY audio generation)

### Rule 13: Voice Correct
- **Check**: Does the voice match the character (female for keiko, male for kuroda)?
- **FAIL if**: wrong gender voice, robotic, garbled
- **Retry action**: verify voice ID is correct for character

### Rule 14: Audio Quality
- **Check**: Is audio clear without artifacts?
- **FAIL if**: clipping, static, echo, too fast/slow
- **Retry action**: adjust rate/pitch parameters

## Global Rules

- **Max retries per scene**: 5 (then flag for human review)
- **Always generate 3 versions**, QA picks best, discard rest
- **Seed increment**: +1 for each retry attempt
- **Log all QA results** to qa_log.json for analysis
- **If AI vision API unavailable**: fall back to file-size heuristics only
