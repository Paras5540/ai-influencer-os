# GitHub deploy — ₹0, server nahi (Vercel se better)

## Vercel kyun nahi
| Zaroorat | Vercel | GitHub Actions |
|---|---|---|
| ffmpeg render (~15s CPU) | ❌ 60s limit, no binary | ✅ |
| Background worker / scheduler | ❌ serverless | ✅ cron |
| Persistent storage | ❌ | ✅ repo/artifacts |
| 3 reels/day | ❌ | ✅ |

Vercel pe sirf **dashboard ka frontend** host ho sakta hai — reels nahi banti. Isliye GitHub.

## Kaise chalta hai

```
GitHub Actions (cron, IST)
  07:00 / 13:00 / 19:00  → python scripts/ci_run.py --task build
  12:30 / 20:30          → --task instagram
  09:00 / 22:00          → --task fanvue
        │
        ├─ ffmpeg + Gemini + Edge TTS → reel (1080x1920)
        ├─ content/<id>/final.mp4 + item.json  (repo me commit)
        ├─ state/ci_ledger.json               (duplicate rok)
        └─ API se post (IG / Fanvue / Shorts)
```

Ledger ki wajah se: ek din me max 3 build, dobara run karne pe duplicate nahi.

## Setup (5 min, sab browser me)

1. **Repo banao** — github.com → New repository → naam `ai-influencer-os` → Private → Create.
2. **Code push** — zip upload karke (ya `git push`), repo me `Dockerfile`, `web/`, `scripts/` sab.
3. **Secrets daalo** — Settings → Secrets and variables → Actions → New repository secret:

| Secret | Zaroori? | Kya |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | script + face-locked images |
| `FAL_KEY` | optional | talking-head video |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | optional | Reels posting |
| `FANVUE_ACCESS_TOKEN` (+ refresh/client) | optional | premium posts |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | optional | Shorts |

4. **Actions on** — Actions tab → `pipeline` → **Run workflow** (task=build) → pehli reel 3 min me.
5. **Pages (optional)** — Settings → Pages → branch `main`, folder `/content` → dashboard-less
   preview gallery: `https://<user>.github.io/ai-influencer-os/`.

## Free limits (asli)

| Cheez | Limit | Hamara use |
|---|---|---|
| Actions minutes | 2000/mo (private repo; public = unlimited) | ~400 min/mo |
| Repo size | 1 GB soft, 100 MB/file | 40 reels (~200 MB) |
| Artifacts | 90 din | backup |
| Cron delay | 5–20 min normal | acceptable |
| **60 din inactivity** | scheduled workflows **auto-disable** | mahine me 1 baar repo kholo / koi commit karo |

## Manual trigger
Actions → `pipeline` → Run workflow → task = `build` / `instagram` / `youtube` / `fanvue`, count = 3.

## Local test
```bash
pip install -r requirements.txt
python scripts/ci_run.py --task build --count 1     # out/ + content/ banega
python scripts/ci_run.py --task collect
```

## Dashboard chahiye to
GitHub pe **read-only** gallery milti hai (Pages). Full dashboard (Generate now, keys, logs) ke liye
Oracle Always Free instance — `docs/FREE_SETUP.md`. Dono ek saath chal sakte hain (same code).
