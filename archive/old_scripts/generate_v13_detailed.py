#!/usr/bin/env python3
"""v13 - Highly detailed donghua CG prompts + parallel generation"""
import asyncio, json, os, subprocess, time, concurrent.futures
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path("/tmp/anime_v13"); OUT.mkdir(parents=True, exist_ok=True)
ARK_KEY = "b7274eee-f993-4d1b-bc76-83ada8d70270"
ARK = "https://ark.cn-beijing.volces.com/api/v3"

with open("/tmp/anime_v7/narration.json") as f:
    ALL = json.load(f)
def group(s, n=15):
    sz = max(1, len(s)//n)
    return ["\uff0c".join(s[i:i+sz]) for i in range(0, len(s), sz)][:n]
NARRS = group(ALL, 15)

MALE_DESC = "a handsome young Chinese man aged 25, sharp jawline, short neat black hair, dark intense warm eyes, wearing a half-unbuttoned white cotton shirt revealing collarbone, athletic build"
FEMALE_DESC = "a beautiful mature Chinese woman aged 35, flowing waist-length silky black hair, jade-like porcelain skin with natural blush, long dense eyelashes, full rose-red lips, wearing a champagne silk nightgown with thin straps, elegant curvy figure"
RENDER = "Rendering: subsurface scattering on skin, ray-traced soft shadows, film grain, cinematic color grading, 8K ultra detailed, shallow depth of field"

SCENES = [
    # 0 - Kiss on sofa
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Close-up shot of {MALE_DESC} passionately kissing {FEMALE_DESC} on a modern leather sofa. His hand cups her face, her fingers grip his shirt collar. Their lips pressed together, eyes closed.
Environment: dimly lit modern living room, warm amber wall sconces, soft bokeh lights in background, silk throw pillows.
Color palette: warm amber, champagne gold, deep mahogany shadows.
{RENDER}.""",

    # 1 - Woman blushing beneath him
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Extreme close-up of {FEMALE_DESC} face from above. She lies beneath him, face deeply flushed crimson, eyes squeezed shut, long eyelashes trembling, lips slightly parted breathing heavily, tiny beads of sweat on temple, silky black hair spread on white silk pillow like spilled ink.
Expression: overwhelmed by desire, vulnerable, biting lower lip.
Lighting: warm candlelight from bedside casting gentle upward shadows, golden rim light on hair edges.
Color palette: warm rose, amber, ivory, deep crimson.
{RENDER}, hyper-detailed skin texture with pores.""",

    # 2 - Kissing her cheek
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Medium close-up of {MALE_DESC} tenderly pressing lips to the cheek of {FEMALE_DESC}. His strong hands rest on her bare shoulders, her skin showing goosebumps. She tilts her head with eyes half-closed, lips trembling.
Environment: modern bedroom with soft warm lamplight, out-of-focus silk curtains in background.
Color palette: soft peach, warm ivory, golden amber.
{RENDER}, visible goosebumps on her shoulders.""",

    # 3 - Whispering in ear
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Intimate extreme close-up of {MALE_DESC} lips barely touching the delicate ear of {FEMALE_DESC}. She blushes intensely, eyes closed tight, a single tear of emotion on her cheek. His breath visible as warm mist. Her jade earring catches candlelight.
Camera: macro lens close-up, extremely shallow depth of field.
Lighting: single warm candle glow from side, dramatic chiaroscuro.
Color palette: deep amber, warm ivory, touches of jade green from earring.
{RENDER}, individual hair strands visible.""",

    # 4 - Carrying bridal style
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Full body medium shot of {MALE_DESC} carrying {FEMALE_DESC} bridal-style in his arms, striding through modern apartment hallway toward bedroom. She clings to his neck, face buried in his chest, long black hair cascading down like waterfall, bare feet dangling, silk nightgown draping elegantly.
Camera: slight low angle, subtle motion blur on background.
Environment: warm tungsten hallway light, golden bedroom glow visible through doorway ahead, wooden floor reflecting light.
Color palette: warm golden amber, soft ivory, rich wood tones.
{RENDER}, realistic cloth physics on silk, hair dynamics.""",

    # 5 - On bed, conflicted
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Medium shot on silk bed, {MALE_DESC} leaning over {FEMALE_DESC}, one hand beside her head, gazing at her intensely. She presses a trembling hand against his chest, expression torn between resistance and desire, lips quivering, eyes glistening with unshed tears.
Environment: luxurious modern bedroom, silk sheets in champagne color, warm dim bedside lamps, gauze curtains filtering moonlight.
Color palette: champagne, warm amber, silver moonlight, deep shadows.
{RENDER}, detailed fabric wrinkles on silk sheets.""",

    # 6 - Passionate kiss on bed
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Close-up of {MALE_DESC} and {FEMALE_DESC} in passionate kiss on silk bed. His shirt pulled open, her nightgown strap slipping off one shoulder. Both hands intertwined gripping the sheets. Silk pillows scattered around.
Lighting: warm golden candlelight from multiple sources, creating soft overlapping shadows.
Color palette: rich gold, warm champagne, rose pink, deep burgundy shadows.
{RENDER}, sweat glistening on skin, wrinkled silk textures.""",

    # 7 - Woman on bed shyly
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Portrait shot of {FEMALE_DESC} sitting on edge of silk bed, nightgown slipping off one shoulder revealing porcelain collarbone, arms crossed shyly covering herself, head turned away with deeply flushed cheeks, long black hair partially covering her face like a veil, bare feet on plush carpet.
Lighting: single warm candle on nightstand casting golden glow, dramatic shadows on far wall.
Environment: modern bedroom, silk sheets rumpled, rose petals scattered on bed.
Color palette: warm candlelight gold, soft rose, ivory skin, deep shadow.
{RENDER}, visible collarbone detail, delicate shoulder.""",

    # 8 - Tender embrace on sheets
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Top-down close shot of {MALE_DESC} and {FEMALE_DESC} lying on champagne silk sheets, him embracing her from behind, his arm wrapped around her waist, lips pressed to her bare shoulder. Her eyes half-closed in bliss, fingers interlaced with his, black hair spread across the pillow.
Lighting: warm amber glow from above, soft shadows in the folds of silk.
Color palette: champagne gold, warm peach, ivory, subtle rose.
{RENDER}, detailed silk fabric folds, intertwined fingers.""",

    # 9 - Curled up shyly
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Medium shot of {FEMALE_DESC} curled up on silk bed facing away, knees drawn up, black hair cascading over bare back and shoulders, nightgown pooled at her waist. {MALE_DESC} sits behind her, one hand gently touching her bare shoulder, expression tender and patient.
Lighting: soft blue moonlight through sheer curtains mixing with warm amber bedside lamp.
Color palette: cool moonlight blue, warm amber, ivory skin, dark hair contrast.
{RENDER}, detailed bare back with subtle spine visible.""",

    # 10 - Kissing shoulder
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Close-up of {MALE_DESC} pressing lips to {FEMALE_DESC} neck and shoulder. Her head tilted back eyes closed, fingers threading through his black hair, body arching slightly. Silk sheet draped across her chest.
Lighting: warm side lighting creating dramatic shadows on skin, hair backlit with golden rim light.
Color palette: warm gold, peach skin tones, dark hair contrast, deep shadows.
{RENDER}, visible neck pulse, detailed hair strands between fingers.""",

    # 11 - Passionate intertwined
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Dramatic shot of {MALE_DESC} and {FEMALE_DESC} locked in passionate embrace on silk bed, bodies close together, silk sheets tangled around them. Both sweating, his forehead pressed to hers, intense eye contact, heavy breathing visible.
Lighting: dramatic warm overhead light with deep shadows, sweat catching light as highlights.
Color palette: warm amber, glistening highlights, deep burgundy shadows, champagne silk.
{RENDER}, sweat droplets on skin, intense emotional expression.""",

    # 12 - Exhausted aftermath
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Wide shot of {MALE_DESC} and {FEMALE_DESC} lying exhausted on rumpled silk sheets, tangled together peacefully. She rests her head on his chest, eyes closed with satisfied serene expression. His arm draped over her, staring at ceiling with peaceful exhaustion. Sheet covering them loosely.
Lighting: soft silver moonlight streaming through sheer curtains, cool blue tones mixing with warm skin.
Color palette: cool moonlight silver, warm skin tones, champagne silk, peaceful blue.
{RENDER}, peaceful facial expressions, rumpled silk texture.""",

    # 13 - Morning sunlight
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Warm morning shot of {MALE_DESC} and {FEMALE_DESC} sleeping peacefully in embrace. Golden morning sunlight streaming through sheer white curtains, casting warm rays across the bed and their faces. Her head nestled in the crook of his neck, his arm protectively around her. Sheet loosely draped.
Lighting: beautiful golden hour sunlight, dust particles visible in light beams, warm and serene.
Color palette: golden sunlight, warm honey, soft white, peaceful ivory.
{RENDER}, sun rays with visible dust motes, peaceful sleeping faces.""",

    # 14 - Tearful embrace
    f"""Chinese donghua 3D CG animation style, IMAX cinematic quality.
Emotional close-up of {FEMALE_DESC} with tears streaming down her cheeks, hugging {MALE_DESC} tightly, her face pressed into his chest. His arms wrap around her protectively, chin resting on her head, expression pained but loving. Morning golden light illuminates them from the window.
Lighting: warm golden backlight from window creating emotional halo, fill light on faces.
Color palette: warm gold, glistening tears catching light, emotional warm tones.
{RENDER}, visible tears with light refraction, emotional micro-expressions.""",
]

VID_PROMPTS = [
    "passionate kiss movement, gentle head tilt, warm light flicker, breathing",
    "blushing deepens, eyelashes flutter, heavy breathing, sweat bead forms",
    "tender kiss on cheek, goosebumps appear, gentle trembling, sigh",
    "whispering breath visible, tear rolls down cheek, earring swings gently",
    "walking motion with woman in arms, hair flowing, nightgown draping",
    "hand trembles against chest, conflicted expression shifts, eyes glisten",
    "passionate kiss deepens, sheet grips tighten, strap slips further",
    "shy turning away, hair falls as veil, candle flame flickers",
    "gentle embrace tightens, fingers interlock, lips on shoulder, peaceful",
    "gentle shoulder touch, she shivers, moonlight shifts across skin",
    "head tilts back, fingers thread through hair, body arches, passionate",
    "foreheads press together, heavy breathing, sweat glistens, intense gaze",
    "peaceful breathing, moonlight slowly shifts, satisfied expressions, serene",
    "morning sunlight moves across faces, dust motes float, peaceful sleep",
    "tears stream down, embrace tightens, emotional trembling, golden light",
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
            print(f"  IMG [{idx:02d}] ✅ {len(d)//1024}KB")
            return str(p), url
        except Exception as e:
            if "400" in str(e) and attempt == 0:
                prompt = prompt.replace("passionately", "tenderly").replace("passionate", "romantic").replace("desire", "emotion").replace("arching", "leaning")
                continue
            if attempt < 2: time.sleep(3); continue
            print(f"  IMG [{idx:02d}] ❌")
            return "", ""
    return "", ""

print(f"{'='*50}\n  v13: DETAILED Donghua CG (Parallel)\n  {len(SCENES)} scenes\n{'='*50}")

# IMAGES - 10 parallel
print("\n--- IMAGES (10 parallel) ---")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(gen_img, p, i): i for i, p in enumerate(SCENES)}
    results = {}
    for f in concurrent.futures.as_completed(futures):
        results[futures[f]] = f.result()

ok = [(i, results[i][0], results[i][1]) for i in sorted(results) if results[i][0]]
print(f"\nImages: {len(ok)}/{len(SCENES)}")

# VIDEOS - submit all at once
print(f"\n--- VIDEOS (all parallel) ---")
vtasks = {}
for i, path, url in ok:
    try:
        r = post("contents/generations/tasks", {"model": "doubao-seedance-1-5-pro-251215",
            "content": [{"type": "image_url", "image_url": {"url": url}}, {"type": "text", "text": VID_PROMPTS[i]}]})
        tid = r.get("id", "")
        if tid: vtasks[i] = tid; print(f"  VID [{i:02d}] submitted")
    except Exception as e:
        print(f"  VID [{i:02d}] submit fail: {str(e)[:40]}")

print(f"Submitted {len(vtasks)} videos. Polling...")
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
                    vpaths.append(str(p)); print(f"  VID [{i:02d}] ✅ {len(d)//1024//1024}MB")
                done.append(i)
            elif sr.get("status") == "failed":
                print(f"  VID [{i:02d}] ❌"); done.append(i)
        except: pass
    for i in done: del remaining[i]
    if remaining and poll % 3 == 0: print(f"  ... {len(remaining)} remaining")

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
subprocess.run(["ffmpeg","-y","-i",str(OUT/"v.mp4"),"-i",narr,"-c:v","copy","-c:a","aac","-b:a","192k","-map","0:v:0","-map","1:a:0","-shortest",str(OUT/"final_v13.mp4")],capture_output=True)
print(f"\n{'='*50}\n  DONE! {os.path.getsize(str(OUT/'final_v13.mp4'))//1024//1024}MB\n{'='*50}")
