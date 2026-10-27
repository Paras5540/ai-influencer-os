# ₹0 setup — sab kuch free (Oct 2026)

Aapka pura system **₹0/month** pe chal sakta hai. Sirf ek compromise: hosting ka choice.

---

## Free options — kaun jeeta

| Option | Cost | Sota hai? | RAM | Disk | Verdict |
|---|---|---|---|---|---|
| **Oracle Cloud Always Free** (Ampere A1) | **₹0 forever** | ❌ | 4 OCPU / 24 GB | 200 GB | 🥇 **BEST** |
| **Google Cloud e2-micro** (always free) | **₹0 forever** | ❌ | 1 GB | 30 GB | 🥈 **FALLBACK** |
| Render free | ₹0 | ✅ 15 min idle | 512 MB | ❌ ephemeral | 🥉 demo only |
| Koyeb / Fly free tiers | ₹0–small | partial | 512 MB | ❌ | ⚠️ risky |
| GitHub Actions (cron se render) | ₹0 | — | 7 GB | ❌ | ⚠️ 6h job limit |
| Apna laptop | ₹0 | band = ruk jaye | — | ✅ | ❌ automation nahi |

**Kyun Oracle:** sota nahi (yahi sabse bada point), 24 GB RAM (ffmpeg ko chahiye), 200 GB disk
(content library badhti rahegi), aur hamesha free. Ek hi friction: signup pe card verification
(₹1 hold, charge nahi) + kabhi kabhi "out of capacity" error.

---

## Option 1 — Oracle Always Free (recommended)

### A. Instance banao (10 min)
1. `cloud.oracle.com` → sign up (card verification ₹1 hold).
2. Compute → Instances → **Create instance**.
3. Image: **Ubuntu 24.04**. Shape: **Ampere / VM.Standard.A1.Flex** → **4 OCPU, 24 GB**.
4. **Always Free eligible** likha dikhna chahiye.
5. SSH key upload karo → Create.
6. Public IP note kar lo.

> "Out of capacity" aaye to dusra Availability Domain try karo, ya 1 OCPU/6 GB se shuru karo
> (baad me badha sakte ho).

### B. Ek command (5 min)
```bash
ssh ubuntu@YOUR_ORACLE_IP
git clone https://github.com/<you>/ai-influencer-os.git
cd ai-influencer-os
bash deploy/free-oracle.sh
```
Script: Docker (ARM) + iptables ports + app deploy (password → volume → **IST** → **3 reels/day**)
+ Cloudflare Tunnel URL + daily backup cron.

### C. Oracle console me firewall (2 min)
Networking → VCN → **Security Lists** → Default → Add Ingress:
- Source `0.0.0.0/0`, protocol TCP, destination port **8000** (ya sirf tunnel use karo, ye skip).

### D. Dashboard (3 min)
Tunnel URL kholo → login (`cat data/.admin_password`) → **Keys** me sirf `GEMINI_API_KEY` → Test → **Generate now**.

---

## Option 2 — GCP e2-micro (agar Oracle capacity na de)

1. GCP → Compute Engine → **e2-micro**, region **us-west1 / us-central1 / us-east1** (yahi free hain).
2. Boot disk: 30 GB standard, Ubuntu 24.04.
3. Firewall: allow HTTP/HTTPS + `tcp:8000`.
4. SSH → `bash deploy/free-gcp.sh`

Ye script **LOW_MEM=1** set karta hai: **720×1280** render, `ultrafast` preset, 2 GB swap.
1 GB RAM pe ffmpeg safely chalta hai, render ~15-20 sec slow hota hai.

---

## Option 3 — Render free (0 card, 2 min, demo)

```bash
# repo push, phir Render -> New -> Blueprint -> render.free.yaml
```
- ✅ Sabse fast start, card nahi
- ❌ 15 min idle pe sota hai (catch-up scheduler jagta hai, par delay)
- ❌ **Persistent disk nahi** → restart pe DB + reels gayab
- ✅ `.github/workflows/keepalive.yml` + `APP_URL` secret → 10 min ping, sotA nahi

Isliye: Render free sirf **try karne** ke liye. Roz 3 reels ka permanent setup Oracle pe.

---

## Free mode me kya badalta hai (aur kya nahi)

| Cheez | Normally | ₹0 mode |
|---|---|---|
| Render size | 1080×1920 | **720×1280** (LOW_MEM=1) — phone pe farak barely dikhta hai |
| Render speed | ~15 s | ~25-40 s |
| Script | Gemini LLM | Gemini free tier (ya template bank) |
| Voice | ElevenLabs (paid) | **Edge TTS** — free, unlimited |
| Image | Gemini nano-banana free tier | same |
| Video | fal (paid) | **ken-burns** (free) — talking head sirf fal se |
| Hosting | VPS ₹350 | Oracle / GCP free |
| **Total** | ₹350–2,600 | **₹0** |

**Catch-up scheduler (free hosting ke liye zaroori):** agar host so gaya tha aur 07:00 ka build miss
hua, to jaagte hi (6 ghante ke andar) wo khud chala jata hai. Test kiya: "missed too long, skipped
07:00 → fired build @ 13:00 (delay 122 min)" ✅

---

## ₹0 key stack (sab free tiers)

| Kaam | Service | Free limit |
|---|---|---|
| Script | Google AI Studio (Gemini) | free tier (per-project limits) |
| Image (face-locked) | Gemini 2.5 Flash Image | free tier |
| Voice | **Edge TTS** (`hi-IN-SwaraNeural`) | **unlimited, no key** |
| Video | ken-burns (ffmpeg) | unlimited |
| Captions | ffmpeg + libass | unlimited |
| Hosting | Oracle Always Free | forever |
| HTTPS URL | Cloudflare Tunnel | free |
| IG / Shorts / Fanvue API | official APIs | free |
| Backup | local disk (7 copies) | free |

Bas ek jagah paisa lagta hai agar aapko **talking-head video** chahiye: fal.ai (₹15-25 per reel).
Ken-burns se bhi reels chalti hain — voice + captions + face same rehta hai.

---

## 10-minute checklist

- [ ] Oracle instance (Ubuntu 24.04, A1, 4 OCPU/24GB)
- [ ] `bash deploy/free-oracle.sh`
- [ ] Tunnel URL + password note
- [ ] Keys: sirf `GEMINI_API_KEY`
- [ ] Character tab: master face dikh raha hai
- [ ] Generate now → reel bani
- [ ] Schedule tab: build 07:00 / 13:00 / 19:00 (default)
- [ ] Backup cron lag gaya (`crontab -l`)
- [ ] Fanvue KYC start (paid tier ke liye, 1-3 din)

---

## Agar kuch atke

| Problem | Fix |
|---|---|
| Oracle "out of capacity" | dusra AD, ya 1 OCPU/6GB se start |
| Tunnel URL nahi aaya | `docker logs influencer-tunnel` |
| Reel 40s+ le rahi | LOW_MEM=1 hai? `docker exec influencer-os env | grep LOW_MEM` |
| Render pe data ud gaya | expected — persistent disk nahi hai, Oracle use karo |
| Scheduler fire nahi hua | `TZ` check: `GET /api/system` me `Asia/Kolkata` dikhna chahiye |
| 512 MB pe OOM | LOW_MEM=1 + `FFMPEG_PRESET=ultrafast` + `FFMPEG_CRF=26` |
