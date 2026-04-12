# 景子老師的課外授業 — Scene Script & Audio Settings

## Characters
| Character | Description | Voice | Rate | Pitch |
|-----------|------------|-------|------|-------|
| **Narrator** | Male narrator | zh-CN-YunxiNeural | -15% | -8Hz |
| **景子 (Keiko)** | 24yo female teacher | zh-CN-XiaoyiNeural | -25% | -5Hz |
| **黒田 (Kuroda)** | 18yo male student | zh-CN-YunxiNeural | -5% | -5Hz |

## Audio Mixing Rules
- **Clean scenes**: Seedance ambient (-10dB) + narrative (full volume)
- **Emotional scenes**: Seedance ambient (-15dB) + narrative + dialogue (-3dB)
- **Explicit scenes**: Mute ambient + narrative + moaning SFX (-5dB)
- Dialogue delayed 1.5s after narrative starts

---

## Scene Script

### 01_ENTRANCE (clean, ambient preserved)
**Narrative:** 景子到任后立即成为学生的偶像。这里是只有男生的学校，二十四岁又有理性美的景子很快有了英正美女的绰号。
**Dialogue:** None
**SFX:** None
**Audio mix:** Seedance ambient (-10dB) + narrative

### 02_TEACHING (clean → strip)
**Narrative:** 自小就对教师充满憧憬，刚在三个月前才考得教师资格的景子，急不及待的就在此颇具名声的英正学院任教。
**Dialogue:** None
**SFX:** None (clean) / moaning SFX (stripped version)
**Audio mix:** Seedance ambient (-10dB) + narrative

### 03_CLOSEUP (clean → strip)
**Narrative:** 景子用毅然的态度上课，受到学生的尊敬。但她不知道，暗处有人正在窥探着她。
**Dialogue:** None
**SFX:** None
**Audio mix:** Seedance ambient (-10dB) + narrative

### 04_CONFRONTATION (clean)
**Narrative:** 横田不满的回答："我有我的教育方针，请不要多管闲事。"景子听着横田下流的说话，全身也在颤抖着。
**Dialogue (景子):** 我是谈正事，横田老师认为春川可以为其他学生牺牲吗？
**SFX:** None
**Audio mix:** Seedance ambient (-15dB) + narrative + dialogue (-3dB, delay 2s)

### 06_AFTER_SCHOOL (clean → strip)
**Narrative:** 放课后的校长室，景子找来了春川作详谈。一下课，景子就对春川的班主任横田老师商量春川的事。
**Dialogue:** None
**SFX:** None
**Audio mix:** Seedance ambient (-10dB) + narrative

### 07_HALLWAY (clean)
**Narrative:** 转眼就到了下一天的五时许，此时校内的学生也全离开了，在日间嘈杂的走廊现也变得静下，就只有景子脚下那高跟鞋所发出的声响。
**Dialogue:** None
**SFX:** Footstep echoes (from Seedance)
**Audio mix:** Seedance ambient (-5dB, louder for footsteps) + narrative

### 08_SHOCK (clean)
**Narrative:** 景子推开了课室的门，只见室内只有五个学生围在一起似是议论着什么。看见推开了门的景子，五人的表情亦变得怪怪的。
**Dialogue (景子):** 只有这里的五个人？春川呢？
**SFX:** Door opening sound
**Audio mix:** Seedance ambient (-10dB) + narrative + dialogue (-3dB, delay 1.5s)

### 09_VULNERABLE (clean → strip)
**Narrative:** 景子感到强烈的压迫感，身体不由得往后退。在学生面前裸露身体，还受到评头品足及下流的说话，景子身上传遍寒意。
**Dialogue (景子):** 不要看……不要看我那羞耻的地方……
**SFX:** Soft crying (clean) / moaning + crying (stripped)
**Audio mix:** Narrative + dialogue (-3dB) + SFX (-8dB)

### 10_CRYING (clean → strip)
**Narrative:** 景子至此就知道事情颇严重。眼中闪出了泪光，声音也变得沙哑。
**Dialogue (景子):** 求求你们放了我，我对你们做了什么，要这样对待我？
**SFX:** Soft sobbing
**Audio mix:** Seedance ambient (-15dB) + narrative + dialogue (-3dB, delay 1.5s)

### 11_POWERPLAY (clean)
**Narrative:** 黑田的冷笑教景子心寒。"到现在还不明白自己的身份，足见头脑尚未成熟。"
**Dialogue (黒田):** 身为宠物竟敢反驳会长的话？
**Dialogue (景子):** 不要打我……我会听话……请不要打。
**SFX:** None
**Audio mix:** Seedance ambient (-15dB) + narrative + dialogues

### 12_MORNING (clean → strip)
**Narrative:** 恶梦般的夜晚过去了。第二日早上，景子站在窗边，目光呆滞，也不去想以后的路。
**Dialogue:** None
**SFX:** Morning ambience
**Audio mix:** Seedance ambient (-5dB, peaceful morning) + narrative

### 13_BRAVE_FACE (clean → strip)
**Narrative:** 景子以缓慢的步伐经过长长的走廊来到最尾的教室。手按在门柄上迟疑了一阵，股起了勇气就用力推开了门。
**Dialogue:** None
**SFX:** None
**Audio mix:** Seedance ambient (-10dB) + narrative

### 14_DETERMINATION (clean)
**Narrative:** 景子深深的吸了一口气。虽不情愿，但现在又要无奈的走在通往这恶梦教室的通道上。
**Dialogue:** None
**SFX:** None
**Audio mix:** Seedance ambient (-10dB) + narrative

### 15_WALKING_AWAY (clean)
**Narrative:** 景子走出屋前时呼出了一口气，今日种种事也如梦幻一样，脑中一片迷惘。景子就惊怕地急急上了计程车离去。
**Dialogue:** None
**SFX:** Evening ambient
**Audio mix:** Seedance ambient (-5dB) + narrative

---

## Explicit Scene Audio (stripped versions)
For stripped scenes, replace clean audio with:
- **Moaning SFX** from assets/voice_real/ at -5dB, looped to video duration
- **Breathing SFX** at -8dB underneath
- **Narrative** continues at full volume over moaning
- **Dialogue** (if any) at -3dB

## Production Notes
- All videos are 5 seconds (Seedance default)
- Narrative often exceeds 5s — need to either speed up narration or loop video
- For final production: stitch all clips + extend some scenes with looped video
- Edge-TTS has no content filter — can generate any Chinese text
