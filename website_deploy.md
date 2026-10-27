# Website deploy — 10 minute setup

Dashboard aapke browser me chalega. Ek baar keys + character set karo, phir schedule auto chalata hai.
Sab kuch free tier pe possible hai.

---

## Kya milta hai

| Tab | Kaam |
|---|---|
| **Dashboard** | reels ready / published / running / failed counters + "Generate now" + live jobs |
| **Reels** | har reel ka video preview, caption edit, aur 3 publish buttons (IG / Shorts / Fanvue) |
| **Character** | master face preview + replace (backup auto) + identity lock |
| **Schedule** | build + publish times (IST), per-task on/off |
| **Keys** | Gemini / fal / ElevenLabs / IG / Fanvue / YouTube — masked save + **Test connections** |
| **Logs** | live stream: kaun sa step chala, kya fallback hua |

Backend: FastAPI + SQLite (`data/app.db`) + 2 background threads (worker + scheduler).
Koi Redis, koi Celery, koi cloud service nahi — ek container me sab.

---

## Option A — Docker (sabse aasan, kisi bhi VPS pe)

```bash
docker build -t influencer-os .
docker run -d --name influencer \
  -p 8000:8000 \
  -e ADMIN_PASSWORD='kuch-strong-password' \
  -v $(pwd)/data:/app/data \
  influencer-os
```
Kholo: `http://SERVER-IP:8000`

`-v` zaroori hai — isse aapke reels, settings aur DB restart ke baad bache rehte hain.

## Option B — Local / laptop (test ke liye)

```bash
pip install -r web/requirements.txt
sudo apt install -y ffmpeg fonts-noto-core
ADMIN_PASSWORD=test123 python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## Option C — Render / Railway (free-ish, no VPS)

1. GitHub pe repo push karo.
2. Render → **New Web Service** → repo choose → it Dockerfile detect kar lega.
3. Env vars: `ADMIN_PASSWORD`, aur keys (ya baad me dashboard se).
4. **Disk add karo** (`/app/data`, 1 GB) — warna har deploy pe data ud jayega.

⚠️ Free instance 15 min idle ke baad sleep hota hai, to **schedule miss ho sakta hai**.
Roz 3 post chahiye to $7/mo starter ya ek ₹350 ka VPS better hai.

## Option D — Cloudflare Tunnel (VPS + free HTTPS)

```bash
cloudflared tunnel --url http://localhost:8000
```
Bina domain, bina SSL setup — public HTTPS URL mil jata hai. Iske baad hi keys daalo.

---

## First run checklist (order important)

1. **Login** — `ADMIN_PASSWORD`.
2. **Character tab** — master face dikh raha hai? Nahi to upload karo. Ye hi identity hai.
3. **Keys tab** — bas `GEMINI_API_KEY` daalo (free tier) → *Test connections* → Gemini OK dikhna chahiye.
   - Voice ke liye kuch nahi chahiye (Edge TTS free).
   - Fanvue/IG baad me, jab account ready ho.
4. **Dashboard** — "Generate now" → 2 reels. 1-3 min. Reels tab me video aa jayegi.
5. **Reels tab** — caption check karo (AI label already add hota hai), phir IG / Shorts / Fanvue.
6. **Schedule tab** — times set karo → Save. Bas, ab auto.

---

## Bina key ke kya hota hai (important)

App **degrade hoke chalta hai**, rukta nahi:

| Step | Key hai | Key nahi hai |
|---|---|---|
| Script | Gemini LLM | built-in Hindi template bank (5 topics, calendar se rotate) |
| Image | face-locked nayi scene | **master image as-is** + slow ken-burns zoom |
| Voice | ElevenLabs (agar diya) | **Edge TTS free** (always) |
| Video | fal talking head | ken-burns motion |
| Captions + render | ffmpeg | ffmpeg |
| Post | IG/Fanvue API | manual download |

⚠️ Fallback mode me master image **jaisi hai waisi hi** reel me aati hai. Agar master revealing shot hai
to public (IG) post ke liye pehle Gemini key daalo — warna wahi shot har reel me jayegi aur IG flag karega.

---

## Security (public internet pe deploy kar rahe ho to)

- `ADMIN_PASSWORD` strong rakho, `changeme` kabhi nahi.
- HTTPS use karo (Cloudflare Tunnel / Caddy / Render default).
- Keys DB me plain text me hain — server access sirf apne paas rakho.
- Public port expose karne ki zaroorat nahi: `-p 127.0.0.1:8000:8000` + tunnel.
- Backup: `data/` folder copy (SQLite + renders). Weekly.

---

## API (agar apna frontend banana ho)

| Method | Path | Kaam |
|---|---|---|
| POST | `/api/login` | `{password}` → cookie |
| GET | `/api/stats` | counters |
| POST | `/api/build` | `{count}` → build jobs |
| GET | `/api/posts` | reels list |
| POST | `/api/publish` | `{post_id, platform}` |
| GET/POST | `/api/settings` | keys |
| POST | `/api/settings/test` | connection test |
| GET/POST | `/api/character` | master + identity (POST = upload) |
| GET/POST | `/api/schedule` | times |
| GET | `/api/logs?after=id` | log stream |
| GET | `/media/...` | video / thumbnails |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg not found` | Docker me already hai; VPS pe `apt install ffmpeg` |
| Captions me `□□□` | `apt install fonts-noto-core` |
| Job 100% pe fail | Logs tab dekho — kaun sa step; aksar key invalid ya quota |
| Video chalta hai par aawaz nahi | browser me click karke play karo (autoplay muted hota hai) |
| Schedule fire nahi hua | server ka timezone IST hona chahiye (`TZ=Asia/Kolkata`) ya Render sleep |
| Purana data ud gaya | `-v` volume / Render disk add nahi kiya |

---

## Live URL — 3 raste (jahan aapko turant URL milega)

> Note: ye system aapke server/account pe host hoga. Main is chat sandbox se permanent public URL
> nahi de sakta (yahan Docker daemon nahi hai, na public IP; sandbox band = URL band).

### 1) VPS + one command (recommended, ~₹350/mo, full control)
```bash
# kisi bhi Ubuntu VPS pe (Hetzner/DigitalOcean/Contabo/Vultr)
git clone <your-repo> && cd ai-influencer-os    # ya zip upload karo
bash deploy/deploy.sh
```
Script khud: strong password generate + save → image build → volume mount `./data` → `TZ=Asia/Kolkata`
→ health wait → schedule seed (build 07:00/13:00/19:00) → URL + password print.
Firewall: `sudo ufw allow 8000/tcp` (ya 80/443 Caddy ke liye).

### 2) Instant HTTPS URL, bina domain (30 second)
```bash
bash deploy/deploy.sh          # app pehle chalao
bash deploy/cloudflared.sh     # -> https://xyz-abc.trycloudflare.com
```
Temporary URL (container jitna jeega). Permanent chahiye to Cloudflare Zero Trust me named tunnel banao
aur `TUNNEL_TOKEN` ke saath `cloudflared tunnel run` chalao — same Caddyfile jaisa kaam.

### 3) Render / Fly (git push, no server)
- **Render**: `render.yaml` repo me hai → New → Blueprint → repo select. Password auto-generate,
  disk 1 GB mount, TZ IST. URL: `https://ai-influencer-os.onrender.com`.
  (Free plan sleep karta hai → schedule miss; starter $7/mo lo.)
- **Fly.io**: `fly.toml` ready (Mumbai `bom`, volume `influencer_data`):
  ```bash
  fly launch --no-deploy --copy-config
  fly volumes create influencer_data --size 1 --region bom
  fly secrets set ADMIN_PASSWORD=$(openssl rand -base64 24)
  fly deploy
  ```
  URL: `https://ai-influencer-os.fly.dev`

### Apna domain + free SSL (Caddy)
```bash
sudo apt install caddy
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile   # domain edit karo
sudo systemctl reload caddy
```

## Timezone = IST (host UTC ho to bhi)
App khud `TZ=Asia/Kolkata` + `time.tzset()` karta hai, isliye schedule hamesha IST me chalta hai.
Verify: dashboard → `GET /api/system` → `{"timezone":"Asia/Kolkata","now":"...","builds_per_day":3}`.

## Default schedule (3 reels/day)
| Task | Time (IST) | Kya |
|---|---|---|
| build | 07:00 | 1 reel |
| build | 13:00 | 1 reel |
| build | 19:00 | 1 reel |
| fanvue | 09:00 | premium post |
| ig | 12:30 | Reels |
| ig | 20:30 | Reels |
| fanvue | 22:00 | premium post |

Schedule tab se time badal sakte ho, ya rows off kar sakte ho.
