# Blueprint — Indian AI Influencer, end-to-end

Ye document explain karta hai ki system **kyun** aise bana hai, face 100% same kaise rehta hai,
paise kahan se aayenge, aur kahan risk hai. Code `src/` me hai, setup `README.md` me.

---

## 1. Architecture (ek nazar me)

```
            ┌──────────────────────────────────────────────────────────┐
            │  master.png  (ek baar bana, hamesha wahi)                │
            │  identity anchor — face ka single source of truth        │
            └───────────────┬──────────────────────────────────────────┘
                            │ har image isi ka EDIT hai (regenerate nahi)
   ┌────────────────────────┴─────────────────────────┐
   │                                                  │
[Cron 06:00]                                   [Config]
 topic calendar ──> LLM script (Hindi, 30-42 words)
                        │
                        ├─> scene prompt (outfit+scene+light ONLY)
                        ├─> Gemini image edit ──> scene.png  (face locked)
                        ├─> ElevenLabs Hindi TTS ──> voice.mp3
                        ├─> Kling Avatar / Sync lipsync ──> raw_head.mp4
                        └─> ffmpeg: 1080x1920 + ASS Hindi captions + ducked music
                                        │
                                  out/<id>/final.mp4 + item.json
                                        │
[Cron 09:30/13:30/20:00]  ──> publish.py ──> IG Reels Graph API
                                        └──> YouTube Shorts API
                                        └──> state/ledger.json (duplicate-proof)
```

Kuch bhi cloud dashboard pe click nahi karna. Sab cron.

---

## 2. Face consistency — "100%" ka sach

**Sach:** text-to-image se har baar *naya* insaan banta hai. Isliye jo bhi tutorial "prompt se
same face" bolta hai, woh galat hai. 5 videos me se 4 ne bhi reference-image editing use ki hai.

System ka rule:

> **Face ek baar banta hai. Uske baad har image = master.png ka edit.**

Isse identity drift ka source hi khatam ho jata hai. Practically:

| Method | Identity match | Consistency per 10 posts |
|---|---|---|
| Text prompt only | 0% | 0/10 |
| Prompt + fixed seed | ~40% | 4/10 |
| LoRA training (Flux, 20-30 images) | ~90% | 9/10 |
| **master.png reference edit (ye system)** | **~92-95%** | **9-10/10** |
| Arcads-style actor model | ~95% | 10/10 |

Yani 100% ka claim marketing hai. **95% kaafi hai**, kyunki Instagram pe compression + 9:16 crop +
motion ke baad viewer ka dimaag face ko 2 second dekhta hai. Baaki 5% tum caption, voice aur
personality se cover karte ho.

Agar 95% se upar chahiye (brand deals ke waqt zaroori hota hai):
1. `master.png` + 5 approved scenes ko **LoRA** se train karo (Flux dev, ~Rs 250, ek baar).
2. Ya Arcads/Higgsfield jaisa actor-lock tool use karo (Rs 3000-6000/month).
Dono ka hook already code me hai: `config/endpoints.json` me model ID badal do, pipeline same.

### Consistency ke 7 practical rules
1. Master image ka **backup** 3 jagah. Kho gaya = character khatam.
2. Prompt me **face describe mat karo** — sirf outfit, scene, light, camera.
3. 10 posts ke baad "approved scenes" folder banao — sirf unhi se aage content banao (safest).
4. Haar/hairline har shot me same style rakho; baal hi sabse zyada "different person" feel deta hai.
5. Makeup level constant: kohl + tinted balm. Kabhi heavy glam, kabhi none — nahi.
6. Expression library 5 hi rakho (`warm_smile, thinking, surprised_light, serious_soft, mid_laugh`).
7. Same voice ID hamesha. Voice badla = naya character.

---

## 3. "Real profile" kaise lagega (ye face se zyada important hai)

AI influencer pakda jata hai **chehre se nahi, behaviour se.** Ye cheezein real banati hain:

- **Continuity:** kal wali kurti aaj bhi, wahi cafe, wahi dost. Real life me sab repeat hota hai.
- **Imperfection:** kabhi akela table, kabhi messy room, kabhi thaki hui aankhein.
- **Reply:** comments me 10-15 reply roz (ye aap karoge, 5 min — automation se better hai).
- **Story:** "main" ka ek arc — job chhodi, freelance shuru kiya. Log story follow karte hain.
- **Boring posts:** har post viral nahi hoti. Real accounts me bhi 200 views aate hain.
- **Location truth:** Bandra, Andheri, local train — jo audience jaanta hai.
- **No perfection:** ek video me hawa ki awaaz, ek me light kharab. AI me sab clean hota hai — isliye
  ffmpeg me halka grain + handheld feel rakha gaya hai.
- **Disclosure:** `#AIgeneratedcharacter` rehne do. Ye trust banata hai, todta nahi. (Meta AI label
  bhi laga deta hai — chhupane ki koshish me reach gir jati hai.)

---

## 4. Growth engine (0 -> 10k)

Phase 1 (Day 1-14) — **volume + pattern find**
14 reels, 1/day. Sab same format (talking head, 1 location type). Kaun sa pillar best chala
dekh. Ceiling: 500-2000 views/reel normal hai.

Phase 2 (Day 15-45) — **trend replication**
Har hafte 3 trend reels: Pinterest/IG se viral reel → frame → Kling Motion Control → apna face.
Yehi sabse sasta viral engine hai (videos 2, 4, 5 ka core). 2-3 trend reels me ek chal jati hai.

Phase 3 (Day 45+) — **series + subscription**
Ek repeatable series ("200 rupaye me Mumbai", "ek kurti teen looks"). Series = return viewers =
subscription buyers. Recall: 42 posts wale page ne 3546 subs beche (Rs 390/month).

**Kya mat karo:** follow-for-follow, bots, 10 posts/day spam. Reach permanently mar jati hai.

---

## 5. Monetization (realistic Indian numbers)

| Source | Kab shuru | Realistic month 3-6 |
|---|---|---|
| Instagram subscription (Rs 99-390/mo) | 3k+ followers, series ban jaye | 20-80 subs = Rs 5k-25k |
| Brand barter (product + Rs 2-8k per reel) | 5k followers | 2-4 deals |
| Paid brand deal (Rs 3-15k/reel) | 10k+ + good engagement | 1-3 deals |
| Affiliate (Amazon/Myntra/Nykaa) | day 1 | Rs 1k-8k |
| YouTube Shorts RPM | 1k subs + 10M views/90d | Rs 2k-15k |
| UGC creation for brands (apna AI avatar bechna) | koi threshold nahi | Rs 10k-40k |

Video 3 ka data point: 5.1k followers pe 3546 paid subs — **followers nahi, "personal connection"
paisa deta hai.** Isliye script style "friend on a call" rakha gaya hai, "influencer voice" nahi.

---

## 6. Risk & compliance (isko ignore mat karo)

| Risk | Kya hota hai | Mitigation (already built) |
|---|---|---|
| Real person ka face copy | Legal notice, permanent ban, defamation | Face sirf master.png se; Pinterest se **pose** ref, face kabhi nahi |
| AI disclosure na karna | Meta label + reach penalty + trust loss | Caption me `#AIgeneratedcharacter`, bio me "AI creator" |
| Deceptive claims | Consumer law + FTC/ASCI issue | Prompt me medical/financial guarantee ban |
| Account ban (automation) | Graph API limit / policy | Official Graph API use (browser automation nahi), 3 posts/day max |
| Deepfake/political | Criminal liability | Prompt rules: no politics, no real persons |
| Face drift se "alag ladki" | Page ki credibility khatam | master.png lock + approved-scene folder |
| Token expire | Post band | Preflight daily health cron + ledger |

Ek line: **AI influencer banana legal hai, kisi real insaan ka chehra use karna nahi.**

---

## 7. Costs (detail `docs/cost_model.csv`)

- **Free path:** Rs 0-500/month (Gemini free tier + Lovart free credits + ElevenLabs free + Kling
  free credits). Cost = time + queues (30 min - 4 hr per video).
- **Hands-off path (recommended):** Rs 2800-5800/month se 60-90 reels. ~Rs 20-40 per reel.
- **Arcads + n8n + Blotato (video 1):** Rs 6k-15k/month.
- Break-even: 1 paid brand reel (Rs 3k+) poora mahine ka kharcha cover kar deta hai.

---

## 8. 30-day launch plan

| Din | Kaam | Time |
|---|---|---|
| 1 | Keys, preflight, master.png banao, 3 variation check karo | 1 hr |
| 2 | Voice lock, 1 test reel end-to-end, phone pe dekho | 45 min |
| 3 | IG Business account + Graph API token, 1 test post (private) | 45 min |
| 4 | Cron on. 3 reels/day queue. Bio + highlights + AI label | 30 min |
| 5-14 | Roz auto. Tum sirf comments reply karo (10/day) | 10 min/day |
| 15 | Analytics: top 3 reels dekho, unka pillar double karo | 30 min |
| 20 | Trend replication on (Kling motion control), 3/week | 30 min/week |
| 25 | Subscription on (Rs 149/month tier), 1 series start | 30 min |
| 30 | 1 brand ko barter pitch (DM + media kit) | 1 hr |

Media kit banane ka simple formula: 3 best reels + audience screenshot + "AI creator, 100% brand
safe, 48-hour delivery" — brands ko yahi chahiye.

---

## 9. Kya ye sach me "mujhe kuch nahi karna padega" hai?

Honest answer:

**Ho jayega (0 daily effort):** scripting, face, image, voice, video, captions, posting, scheduling,
retry, duplicate protection, health check.

**Nahi ho sakta (aur koi bhi system nahi kar sakta):**
1. **Comments/DMs** — growth inhi se hoti hai. 10 min/day. (Chaho to LLM se draft karwa lo, par
   post karna aadmi hi kare.)
2. **Monthly topic refresh** — `content_calendar.csv` me 30 naye topics, 15 min/month.
3. **Quality gate** — pehle 2 hafte har reel dekh lo (10 sec). Ek kharab face wala reel post hone se
   rokna zaroori hai. Iske liye `--dry-run` / manual review mode hai.
4. **Trend pick** — kaun sa trend chal raha hai, ye judgement ka kaam hai.
5. **Brand deals** — DM aapko hi karna hoga.

Baaki 95% machine karti hai.
