#!/usr/bin/env python3
"""v14 - Fixed scene asset + character asset + no Chinese text + detailed + parallel"""
import asyncio, json, os, subprocess, time, concurrent.futures
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path("/tmp/anime_v14"); OUT.mkdir(parents=True, exist_ok=True)
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)
def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

# ═══════════════════════════════════════════════════════
# FIXED ASSETS - identical in EVERY prompt for consistency
# ═══════════════════════════════════════════════════════

STYLE = """Donghua 3D CG animation style, IMAX cinematic quality, Unreal Engine 5 render, ray-traced global illumination, 8K ultra detailed, film grain, cinematic color grading, shallow depth of field"""

MALE_ASSET = """a handsome young East Asian man aged 25, sharp defined jawline, short neat jet-black hair swept to the right, dark brown intense warm eyes with double eyelids, light stubble on chin, straight nose, defined collarbone visible, athletic lean build, wearing a half-unbuttoned white cotton shirt with sleeves rolled up to elbows"""

FEMALE_ASSET = """a beautiful mature East Asian woman aged 35, flowing waist-length silky jet-black hair with subtle waves, jade-like porcelain skin with natural warm blush on high cheekbones, long dense curved eyelashes, almond-shaped gentle eyes with dark brown irises, full naturally rose-red lips, small delicate nose, wearing a champagne-colored silk nightgown with thin spaghetti straps and lace trim at neckline, elegant hourglass figure"""

SCENE_ASSET = """modern luxury bedroom: king-size bed with champagne silk sheets and two ivory silk pillows, dark charcoal gray walls, two warm amber glass wall sconces flanking a abstract gold-frame painting above headboard, floor-to-ceiling window on right wall with sheer white organza curtains, mahogany nightstand with single lit candle in crystal holder, plush cream wool carpet, subtle rose petals scattered on bed and floor"""

# ═══════════════════════════════════════════════════════
# 15 SCENES - each uses EXACT same assets above
# ═══════════════════════════════════════════════════════

SCENES = [
    # 0
    f"""{STYLE}. Close-up shot.
{MALE_ASSET} passionately kissing {FEMALE_ASSET} on a modern leather sofa in the living room adjacent to the bedroom. His right hand cups her face, left hand on her waist. Her fingers grip his shirt collar. Lips pressed together, both eyes closed.
Lighting: warm amber side light from floor lamp, soft fill light from hallway. Color palette: warm amber, champagne gold, deep mahogany shadows.
{SCENE_ASSET} visible through open doorway in background, blurred.""",

    # 1
    f"""{STYLE}. Extreme close-up from above.
{FEMALE_ASSET} lying on the champagne silk sheets, face deeply flushed crimson, eyes squeezed shut, long eyelashes trembling, lips slightly parted breathing heavily, tiny beads of sweat glistening on her temple, black hair spread across ivory silk pillow like spilled ink.
Expression: overwhelmed, vulnerable, biting lower lip.
{SCENE_ASSET}. Lighting: warm candlelight from mahogany nightstand casting gentle upward shadows, golden rim light on hair edges from wall sconce.""",

    # 2
    f"""{STYLE}. Medium close-up.
{MALE_ASSET} tenderly pressing his lips to the cheek of {FEMALE_ASSET}. His strong hands rest on her bare shoulders above the nightgown straps, her porcelain skin showing goosebumps. She tilts head with half-closed eyes, lips trembling.
{SCENE_ASSET}. Lighting: soft warm glow from both wall sconces, out-of-focus sheer curtains in background.""",

    # 3
    f"""{STYLE}. Macro close-up, extremely shallow depth of field.
{MALE_ASSET} lips barely touching the delicate ear of {FEMALE_ASSET}. She blushes intensely, eyes closed tight, a single tear of emotion on her cheek, small jade earring catching candlelight. His warm breath creating slight mist.
{SCENE_ASSET}. Lighting: single warm candle glow from crystal holder on nightstand, dramatic chiaroscuro on their faces.""",

    # 4
    f"""{STYLE}. Full body medium shot, slight low angle.
{MALE_ASSET} carrying {FEMALE_ASSET} bridal-style in his arms, striding from hallway into the bedroom. She clings to his neck, face against his chest, long black hair cascading down like waterfall, bare feet dangling, silk nightgown draping elegantly.
{SCENE_ASSET} visible ahead with warm amber glow from wall sconces. Subtle motion blur on background. Mahogany floor reflecting warm light.""",

    # 5
    f"""{STYLE}. Medium shot on bed.
{MALE_ASSET} leaning over {FEMALE_ASSET} on the king-size bed with champagne silk sheets. One hand beside her head on ivory pillow, gazing at her intensely. She presses a trembling hand against his bare chest visible through open shirt, expression torn between resistance and desire, eyes glistening.
{SCENE_ASSET}. Lighting: warm amber from both wall sconces, candlelight from nightstand.""",

    # 6
    f"""{STYLE}. Close-up on bed.
{MALE_ASSET} and {FEMALE_ASSET} in passionate kiss on the champagne silk sheets. His white shirt pulled fully open revealing chest, her nightgown strap slipped off one shoulder revealing collarbone. Both hands intertwined gripping the silk sheets. Ivory pillows scattered.
{SCENE_ASSET}. Lighting: warm golden candlelight creating soft overlapping shadows, rose petals around them.""",

    # 7
    f"""{STYLE}. Portrait shot.
{FEMALE_ASSET} sitting on edge of king-size bed, nightgown slipping off one shoulder revealing porcelain collarbone and shoulder, arms crossed shyly covering herself, head turned away with deeply flushed cheeks, long black hair partially covering her face like a veil, bare feet on plush cream carpet.
{SCENE_ASSET}. Lighting: single candle on mahogany nightstand casting golden glow, dramatic shadows on charcoal wall behind her. Rose petals on bed beside her.""",

    # 8
    f"""{STYLE}. Top-down close shot.
{MALE_ASSET} and {FEMALE_ASSET} lying on champagne silk sheets, him embracing her from behind, his arm wrapped around her waist over the silk nightgown, lips pressed to her bare shoulder. Her eyes half-closed in bliss, her fingers interlaced with his, black hair spread across ivory pillow.
{SCENE_ASSET}. Lighting: warm amber glow from wall sconces above, soft shadows in silk folds.""",

    # 9
    f"""{STYLE}. Medium shot.
{FEMALE_ASSET} curled up on champagne silk sheets facing away, knees drawn up, black hair cascading over bare shoulders above nightgown, back partially exposed. {MALE_ASSET} sits behind her, one hand gently touching her bare shoulder, expression tender and patient, shirt hanging open.
{SCENE_ASSET}. Lighting: cool blue moonlight through sheer organza curtains mixing with warm amber from single wall sconce.""",

    # 10
    f"""{STYLE}. Close-up.
{MALE_ASSET} pressing lips to {FEMALE_ASSET} neck and shoulder above the nightgown strap. Her head tilted back eyes closed, fingers threading through his short black hair, body arching slightly. Champagne silk sheet draped loosely across them.
{SCENE_ASSET}. Lighting: warm side light from wall sconce creating dramatic shadows on skin, hair backlit with golden rim light from candle.""",

    # 11
    f"""{STYLE}. Dramatic shot.
{MALE_ASSET} and {FEMALE_ASSET} in passionate embrace on the king-size bed, champagne silk sheets tangled around them. Both with sheen of sweat, his forehead pressed to hers, intense eye contact, heavy breathing visible. Rose petals stuck to damp skin.
{SCENE_ASSET}. Lighting: dramatic warm overhead from both wall sconces, sweat catching light as highlights, deep burgundy shadows.""",

    # 12
    f"""{STYLE}. Wide shot.
{MALE_ASSET} and {FEMALE_ASSET} lying exhausted on rumpled champagne silk sheets of king-size bed, tangled together peacefully. She rests her head on his bare chest, eyes closed with serene satisfied expression. His arm draped over her, staring at ceiling peacefully. Sheet covering them loosely.
{SCENE_ASSET}. Lighting: soft silver moonlight through sheer organza curtains, cool blue tones on their skin, candle on nightstand burned low.""",

    # 13
    f"""{STYLE}. Warm morning shot.
{MALE_ASSET} and {FEMALE_ASSET} sleeping peacefully in embrace on king-size bed with champagne silk sheets. Golden morning sunlight streaming through sheer white organza curtains, casting warm rays across their faces and the bed. Her head nestled in crook of his neck, his arm protectively around her.
{SCENE_ASSET}. Lighting: beautiful golden hour sunlight with visible dust motes in beams, warm and serene. Candle on nightstand extinguished, thin wisp of smoke.""",

    # 14
    f"""{STYLE}. Emotional close-up.
{FEMALE_ASSET} with tears streaming down her porcelain cheeks, hugging {MALE_ASSET} tightly, her face pressed into his chest, fingers gripping his white shirt. His arms wrap around her protectively, chin resting on her head, expression pained but loving. Morning golden light from window behind them.
{SCENE_ASSET}. Lighting: warm golden backlight from window creating emotional halo around them, soft fill light on their faces.""",
]

VID_PROMPTS = [
    "passionate kiss, gentle head tilt, warm light flicker, soft breathing",
    "blushing deepens, eyelashes flutter, heavy breathing, sweat bead forms on temple",
    "tender kiss on cheek, goosebumps appear on shoulders, gentle trembling",
    "whispering breath visible as mist, tear rolls down cheek, jade earring swings",
    "walking motion carrying woman, hair flowing like waterfall, nightgown draping",
    "trembling hand presses against chest, conflicted expression shifts, eyes glisten",
    "passionate kiss deepens, sheet grips tighten, nightgown strap slips further",
    "shy turning away, hair falls as veil over face, candle flame flickers",
    "gentle embrace tightens from behind, fingers interlock, lips press to shoulder",
    "gentle touch on bare shoulder, she shivers, moonlight shifts across her skin",
    "head tilts back in pleasure, fingers thread through hair, body arches",
    "foreheads press together, heavy breathing, sweat glistens, intense eye contact",
    "peaceful breathing rises and falls, moonlight slowly shifts, candle flickers low",
    "morning sunlight moves across sleeping faces, dust motes float in beam",
    "tears stream down, embrace tightens desperately, emotional trembling, golden halo light",
]

def post(endpoint, body):
    r = Request(f"{ARK}/{endpoint}", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {ARK_KEY}", "Content-Type": "application/json"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def get_json(url):
    r = Request(url, headers={"Authorization": f"Bearer {ARK_KEY}"})
    with urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def dl(url):
    with urlopen(Request(url), timeout=300) as resp:
        return resp.read()

def gen_img(prompt, idx):
    for attempt in range(3):
        try:
            r = post("images/generations", {"model": "doubao-seedream-4-5-251128", "prompt": prompt, "response_format": "url", "size": "1920x1920"})
            url = r["data"][0]["url"]
            d = dl(url)
            p = OUT / f"img_{idx:02d}.png"; p.write_bytes(d)
            print(f"  IMG [{idx:02d}] OK {len(d)//1024}KB")
            return str(p), url
        except Exception as e:
            if "400" in str(e) and attempt == 0:
                prompt = prompt.replace("passionately", "tenderly").replace("passionate", "romantic").replace("desire", "emotion").replace("arching", "leaning").replace("bare", "").replace("exposed", "")
                continue
            if attempt < 2: time.sleep(3); continue
            print(f"  IMG [{idx:02d}] FAIL")
            return "", ""
    return "", ""

print(f"{'='*50}\n  v14: Scene+Character Assets, Detailed, Parallel\n  No Chinese text references\n  {len(SCENES)} scenes\n{'='*50}")

# IMAGES - 10 parallel
print("\n--- IMAGES (10 parallel) ---")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(gen_img, p, i): i for i, p in enumerate(SCENES)}
    results = {}
    for f in concurrent.futures.as_completed(futures):
        results[futures[f]] = f.result()

ok = [(i, results[i][0], results[i][1]) for i in sorted(results) if results[i][0]]
print(f"\nImages: {len(ok)}/{len(SCENES)}")

# VIDEOS - all parallel
print(f"\n--- VIDEOS (all parallel) ---")
vtasks = {}
for i, path, url in ok:
    try:
        r = post("contents/generations/tasks", {"model": "doubao-seedance-1-5-pro-251215",
            "content": [{"type": "image_url", "image_url": {"url": url}}, {"type": "text", "text": VID_PROMPTS[i]}]})
        tid = r.get("id", "")
        if tid: vtasks[i] = tid; print(f"  VID [{i:02d}] submitted")
    except Exception as e:
        print(f"  VID [{i:02d}] fail: {str(e)[:40]}")

print(f"Submitted {len(vtasks)}. Polling...")
vpaths = []
remaining = dict(vtasks)
for poll in range(90):
    if not remaining: break
    time.sleep(10)
    done = []
    for i, tid in list(remaining.items()):
        try:
            sr = get_json(f"{ARK}/contents/generations/tasks/{tid}")
            if sr.get("status") == "succeeded":
                vu = sr.get("content", {}).get("video_url", "")
                if vu:
                    d = dl(vu); p = OUT / f"vid_{i:02d}.mp4"; p.write_bytes(d)
                    vpaths.append(str(p)); print(f"  VID [{i:02d}] OK {len(d)//1024//1024}MB")
                done.append(i)
            elif sr.get("status") == "failed":
                print(f"  VID [{i:02d}] FAIL"); done.append(i)
        except: pass
    for i in done: del remaining[i]

vpaths.sort()
print(f"\nVideos: {len(vpaths)}/{len(vtasks)}")
if not vpaths: print("ERROR!"); exit(1)

# AUDIO
print(f"\n--- AUDIO ---")
import edge_tts
from pydub import AudioSegment
async def audio():
    c = AudioSegment.empty()
    for i, t in enumerate(NARRS[:len(vpaths)]):
        f = str(OUT / f"a{i}.mp3")
        await edge_tts.Communicate(t, voice="zh-CN-YunxiNeural", rate="-15%", pitch="-8Hz").save(f)
        c += AudioSegment.from_mp3(f) + AudioSegment.silent(500)
    p = str(OUT / "narr.mp3"); c.export(p, format="mp3", bitrate="128k")
    print(f"  {len(c)/1000:.1f}s"); return p
narr = asyncio.run(audio())

# STITCH
print(f"\n--- STITCH ---")
with open(OUT/"c.txt","w") as f:
    for v in vpaths: f.write(f"file '{v}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(OUT/"c.txt"),"-c:v","libx264","-preset","fast","-crf","23","-an",str(OUT/"v.mp4")],capture_output=True)
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,"-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0","-shortest",str(OUT/"final_v14.mp4")],capture_output=True)
print(f"\n{'='*50}\n  DONE! {os.path.getsize(str(OUT/'final_v14.mp4'))//1024//1024}MB\n{'='*50}")
