# AI Influencer OS — dashboard + full automation

**Web app** (FastAPI + SQLite) jahan sab kuch ek jagah hai: character lock, keys, reel generation,
captions, Instagram / YouTube / Fanvue publishing, schedule aur live logs.
Ek baar setup → phir sab auto.

> **₹0 + zero server (fastest):** GitHub Actions cron → **`docs/GITHUB_DEPLOY.md`** (Vercel pe
> ffmpeg nahi chalta, isliye GitHub). Dashboard: `docs/FREE_SETUP.md` (Oracle).
> **₹0 with dashboard:** Oracle Always Free + `bash deploy/free-oracle.sh`
> → **`docs/FREE_SETUP.md`** · 720p low-memory mode + catch-up scheduler built in.
> Paid-but-zero-jugaad: ₹350 VPS → `docs/BEST_OPTION.md` · others: `docs/website_deploy.md`

```bash
pip install -r web/requirements.txt
ADMIN_PASSWORD=test123 python -m uvicorn web.app:app --port 8000   # -> http://localhost:8000
# ya: docker build -t influencer-os . && docker run -p 8000:8000 -e ADMIN_PASSWORD=x -v $(pwd)/data:/app/data influencer-os
```

| Tab | Kaam |
|---|---|
| Dashboard | counters + "Generate now" + live jobs |
| Reels | video preview, caption edit, publish (IG / Shorts / Fanvue) |
| Character | master face + replace (backup auto) |
| Schedule | build + publish times (IST) |
| **APIs** | **30 settings, 7 groups** — Gemini, ElevenLabs, fal, IG, YouTube, Fanvue, LLM gateway, automation. “Get key ↗” link + Test connections + Download .env |
| Deploy | timezone, builds/day, disk, render mode, live checks, one-command deploy, .env download |
| Logs | live step-by-step stream |

Bina kisi key ke bhi chalta hai (master face + free Edge TTS + captions). Keys daalne pe AI scene
aur talking-head video on ho jate hain.

Ek face (Riya Malhotra, 23, Mumbai), roz naye reels public pe, aur **Fanvue premium tier** bhi
automated. Aapko roz karna: kuch nahi (chat 10 min optional).

```
06:00  build   -> script -> face-locked image -> Hindi voice (FREE) -> talking video
                  -> 1080x1920 + burned Devanagari captions
09:00  Fanvue  -> glamour set upload -> POST /v1/posts (price + publishAt)  [API]
12:30  IG      -> Reels
20:30  IG      -> Reels + YouTube Shorts
22:00  Fanvue  -> scheduled PPV drop + weekly mass DM                      [API]
```

---

## Do tiers, ek face

| Tier | Platform | Content | Automation |
|---|---|---|---|
| Public funnel | Instagram Reels, YouTube Shorts | fully clothed, glam, lifestyle | 100% auto |
| **Premium** | **Fanvue** (AI accounts allowed) | lingerie / boudoir / implied | ~95% auto via Fanvue API |
| Backup | Telegram channel | teaser + link | bot API |

⚠️ **OnlyFans pe ye nahi chalega** — OF sirf verified real creator ka AI content allow karta hai.
Fictional AI girl ka OF possible nahi. Detailed comparison: `docs/premium_business.md`.

⚠️ **Instagram pe nudity nahi** — Meta AI-generated nudity bhi remove karta hai. Bio link allowed,
caption me bechna nahi. Isliye public tier SFW hai.

---

## Folder map

```
config/character_v5_locked.json    LOCKED character (master = user ki exact image)  <- DEFAULT
config/character_v5.json           v5 (rebuild variant) — ab use NAHI ho raha
config/character_v4.json           Riya v4 (golden-tan archetype) — alternate
config/character_v3.json           Riya v3 (girl-next-door look) — alternate
config/character_v2_premium.json   Riya v2 (glam/gold look) — alternate
config/character.json              v1 character (Ira) — soft lifestyle niche
config/endpoints.json              har model/provider yahan (edge/gemini/fal/fanvue)
config/content_calendar.csv        30 din ke topics
prompts/01d_face_master_v5.txt     master face prompt v5 (ek baar) — CURRENT
prompts/01c_face_master_v4.txt     master face prompt v4
prompts/01b_face_master_v3.txt     master face prompt v3
prompts/01_face_master.txt         master face prompt v1
prompts/02_scene_edit.txt          scene edit template (face lock)
prompts/03_script_brain.md         script + hook + caption brain
prompts/05_premium_prompts.md      glamour prompt library (tasteful)
src/01_build_character.py          master face + 6-angle sheet
src/02_generate_batch.py           daily batch builder
src/05_publish.py                  IG Reels + YouTube Shorts
src/06_fanvue.py                   Fanvue: upload + post + price + schedule + mass DM
src/lib/free_stack.py              FREE: edge-tts, pollinations
src/lib/voice.py                   edge (free) / elevenlabs (paid) dispatcher
docs/free_stack.md                 har step ka best free option (bundles A/B/C)
docs/premium_business.md           platform research, pricing, legal (India), launch plan
docs/reference_photo_policy.md     real photo aaye to kya karna (style copy, identity nahi)
docs/GITHUB_DEPLOY.md              ₹0 serverless: GitHub Actions cron + Pages
docs/FREE_SETUP.md                 ₹0 hosting (Oracle / GCP / Render) + free stack
scripts/ci_run.py                  GitHub Actions runner (build / publish / collect)
docs/BEST_OPTION.md                paid-but-simple deploy (₹350 VPS)
deploy/free-oracle.sh              one-command ₹0 install (Oracle ARM)
deploy/free-gcp.sh                 one-command ₹0 install (GCP 1GB, LOW_MEM)
docs/website_deploy.md             deploy alternatives (Render/Fly/Oracle) + checklist
deploy/bootstrap.sh                one-line installer (Docker + swap + ufw + tunnel)
deploy/backup.sh                   daily data backup (7 copies)
web/                               FastAPI dashboard (app, worker, pipeline, UI)
Dockerfile                         one-command deploy
```

---

## Setup (ek baar, ~25 min)

```bash
cp .env.example .env          # keys; sab free tier se shuru ho sakta hai
pip install -r requirements.txt
sudo apt install -y ffmpeg fonts-noto-core
python src/00_preflight.py
```

**Free voice (default):** kuch nahi chahiye — Edge TTS unlimited hai.
Test: `files/voice_sample_free_edge_tts.mp3`.

### 1. Character
`assets/character_v6/master.png` = user ki EXACT image, zero modification (sha256 verified).
Ye hi identity anchor hai — koi regenerate/crop/enhance nahi.
Config me default bhi v3 hai (`.env` -> CHARACTER_CONFIG / CHARACTER_DIR).
Naya banana ho to: `python src/01_build_character.py --config character_v5_locked.json --dir character_v6  # (already done — master locked)`

### 2. Fanvue (premium tier)
1. fanvue.com pe creator account + **KYC** (AI account bhi KYC karta hai).
2. Settings → Developer/API → app register → OAuth PKCE se access token lo.
3. `.env` me `FANVUE_ACCESS_TOKEN` (ya refresh token + client id/secret).
4. Verify: `python src/06_fanvue.py --check`
5. Test post: `python src/06_fanvue.py --post --file out/x/final.mp4 --text "test" --dry-run`

### 3. Automation
VPS: `crontab -e` ← `deploy/crontab.txt`
Ya GitHub Actions: `.github/workflows/daily.yml` (free, laptop band ho to bhi chalta hai)

---

## Commands

```bash
python src/02_generate_batch.py --count 2          # build 2 reels
python src/05_publish.py --limit 1                 # IG + Shorts
python src/06_fanvue.py --queue --price 699        # premium queue -> Fanvue PPV posts
python src/06_fanvue.py --post --file x.mp4 --at 2026-10-28T22:00:00+05:30
python src/06_fanvue.py --mass --text "welcome 🖤"  # welcome / win-back DM
```

---

## Face consistency (v2 rules)

1. `master.png` ek baar. Har image uska **edit**.
2. Prompt me face describe mat karo — sirf outfit, scene, light, camera.
3. Garam-ish set (lingerie) ke liye: **SeaArt/Tensor pe free LoRA train karo** (150/50 credits
   daily) — uske baad drift zero.
4. Ek voice, ek hair colour, ek makeup level.
5. Har 10 posts pe "approved set" folder banao; sirf usi se aage.

---

## Compliance (chhota par zaroori)

- `#AIgeneratedcharacter` hamesha (code daalta hai). Fanvue ka AI tag compulsory.
- Real person ka face/cheekh kabhi nahi. Deepfake = ban + case.
- "18 just turned", school uniform, baby voice = instant ban.
- India: IT Act 67/67A + IT Rules SGI labelling. Paisa foreign platform se aata hai → PAN/ITR.
  Detail `docs/premium_business.md` section 6.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Captions me boxes | `sudo apt install fonts-noto-core` |
| Edge TTS silent | `pip install -U edge-tts` (Microsoft endpoint change hota rehta hai) |
| Fanvue 401 | token expire — refresh token ya re-OAuth |
| Fanvue 400 on post | price ≥ 300 cents, `audience` required |
| Media stuck `processing` | 30-60s lagta hai; moderation slow ho to 5 min |
| Face har reel me different | prompt se face words hatao + LoRA |
| IG publish error | token 60 din me expire, account Business/Creator hona chahiye |
