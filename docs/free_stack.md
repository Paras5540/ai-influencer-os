# Free stack — har step ka best free option (verified Oct 2026)

Sab kuch free rakhna possible hai — **ek jagah chhod ke**: free video me API nahi hoti, to us step pe
machine ki jagah aapka 1 click lagta hai. Neeche 3 bundle diye hain, aap chuno.

---

## 1. Voice — 100% free, unlimited ✅ (best upgrade)

| Option | Limit | Verdict |
|---|---|---|
| **Microsoft Edge TTS** (`hi-IN-SwaraNeural` / `hi-IN-AnanyaNeural`) | unlimited, no key, no signup | **USE THIS.** Neural quality, 322 voices, Hindi female |
| ElevenLabs free | 10k chars/month (~8 reels) | emotion better, but cap khatam ho jata hai |
| Google Cloud TTS free | 1M chars/month (WaveNet) | good, card chahiye |
| Kokoro / local | unlimited | Hindi support weak |

`src/lib/free_stack.py` me `edge_tts()` ready hai. Test file: `files/voice_sample_free_edge_tts.mp3`.
Rate `+8%`, pitch `+15Hz` — isse awaaz zyada "young/soft" lagti hai. Voice change mat karna.

---

## 2. Image (face-locked) — free options

| Option | Free limit | Face lock | Automation |
|---|---|---|---|
| **Gemini 2.5 Flash Image** (nano-banana, AI Studio) | free tier ~ daily cap | ✅ reference edit | ✅ API |
| **Pollinations** | keyless, rate-limited | partial (`kontext` + `image=` URL) | ✅ API, no key |
| **SeaArt** | 150 credits/day + character lock + LoRA training | ✅ best free | ❌ manual |
| **Tensor.Art** | 50 credits/day, **free LoRA training** | ✅ best | ❌ manual (TAMS paid) |
| **Lovart** | 30 credits/day | ✅ | ❌ manual |
| Leonardo | 150 tokens/day | ✅ | ❌ manual |

**Rule:** 90% images API se (Gemini) — kyunki wahi automate hota hai. Jo shoot "hero set" hai
(lingerie set, festival look) usko SeaArt/Tensor pe manually banao — **wahan LoRA train kar lo
(free), uske baad face drift zero ho jata hai.** LoRA ek baar train, hamesha use.

---

## 3. Video (talking / motion) — yahan free aur automation ka conflict hai

| Option | Free | API? | Notes |
|---|---|---|---|
| **fal.ai sandbox — Wan 3** | 5 generations / 24h | ❌ (browser) | card on file chahiye, 720p, sound ke saath |
| **Kling AI** | ~3-5 credits/day | ❌ | motion control, watermark on free |
| **Hailuo / MiniMax** | daily reset | ❌ | fast |
| **Higgsfield** | daily credits | ❌ | best trend/dance replication |
| **Google Flow (Veo 3.1 Fast)** | 180 credits/mo (1000/mo Jio SIM) | ❌ | dialogue video best |
| **wan.video** | daily check-in | ❌ | Character Swap = apna face + reference reel |
| **kie.ai Kling Motion Control** | 80 credits ≈ 1 job | ✅ paid API | ₹ me sasta |
| **VisionStory** | 10 credits + weekly bonus | ✅ API | talking photo, 30s free |
| **fal.ai paid** | — | ✅ | Wan 3 720p ≈ $0.10/sec → 5s ≈ ₹45 |

**Sach:** 100% free + 100% automation video me possible nahi hai. Teen raste:

- **A. ₹0/month** — video roz manually: Kling/Wan pe 2 min ka 1 click. Baaki sab auto.
- **B. ₹700-1500/month** — fal/vidu API se video auto. Kuch bhi click nahi. (recommended)
- **C. ₹0 + technical** — free Colab/Kaggle pe Wan 2.2 Animate / LatentSync self-host. Free but
  har run ~20-40 min, github action se trigger karna fragile. Sirf agar aapko tech shauk ho.

---

## 4. Render, captions, thumbnail — 100% free ✅

ffmpeg + libass + Noto Devanagari. 1080x1920, burned Hindi captions, music ducking, film grain.
Sab `src/lib/media.py` me. Koi API, koi limit nahi.

---

## 5. Automation + hosting — 100% free ✅

| Option | Free | Note |
|---|---|---|
| **GitHub Actions** | 2000 min/month private repo, unlimited public | cron 3x/day, ₹0 |
| Oracle Cloud Free Tier | 4 ARM cores forever | overkill but free |
| Render/Fly free | 750 hrs | sleep issues |
| VPS | ₹350-600/mo | most predictable |

---

## 6. Publishing — 100% free ✅

| Platform | Cost | Automation |
|---|---|---|
| Instagram Reels (Graph API) | free | ✅ `src/05_publish.py` |
| YouTube Shorts (Data API) | free quota | ✅ same file |
| **Fanvue (premium tier)** | free API | ✅ `src/06_fanvue.py` — media upload + `POST /v1/posts` + `publishAt` + mass DM |
| Telegram channel | free | ✅ bot API (extra income tier) |

---

## 7. LLM / "100M free tokens" — ye bottleneck hi nahi hai

Ek reel ka script ~200 tokens. 100M tokens = **~5 lakh reels** ka scripting. Matlab tokens free hain
to bhi video paisa khayega. Tokens ka asli use: **fan chat replies + caption variants + 100 hooks
generate karke best pick** (jo actually revenue badhata hai).

Koi bhi OpenAI-compatible free gateway chalega (`OPENAI_BASE_URL` + `OPENAI_API_KEY`):
Groq free (1k req/day), Gemini free tier, OpenRouter free models, ya aapka 100M-token wala provider.
`src/lib/providers.py` me `gemini_text()` ki jagah 10-line adapter — bolo to main wire kar dun,
bas provider ka naam + base URL bata do.

---

## Final: 3 bundles

| | Bundle A — ₹0 | Bundle B — ₹900/mo | Bundle C — ₹2800/mo |
|---|---|---|---|
| Images | Gemini free + SeaArt manual LoRA | Gemini free | nano-banana paid + LoRA |
| Voice | Edge TTS | Edge TTS | ElevenLabs |
| Video | Kling/Wan free (1 click) | fal API auto | fal + Kling Pro |
| Captions/render | ffmpeg | ffmpeg | ffmpeg |
| Hosting | GitHub Actions | GitHub Actions | VPS |
| Publish | Fanvue + IG API | same | same |
| **Aapka time** | **~2 min/day** | **0** | **0** |
| **Quality** | 7/10 | 8/10 | 9.5/10 |

Shuru Bundle B se karo. Pehla mahina ₹900 kharch, ek subscription (₹749) se hi cover ho jata hai.
