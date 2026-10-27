# BEST OPTION — meri final recommendation (Oct 2026)

> **₹0 chahiye?** → **`docs/FREE_SETUP.md`** (Oracle Always Free / GCP e2-micro). Wahan bhi
> sab automatic hai, bas render 720p hota hai aur hosting free hai.
> Neeche wala ₹350/mo option tab best hai jab aap 1080p + zero jugaad chahte ho.

**Chuna hua: ₹350/mo VPS + `deploy/bootstrap.sh` + Cloudflare Tunnel (free HTTPS)**

Ek hi command me pura system live ho jata hai, 24x7 chalta hai, aur roz 3 reels banata hai.

---

## Kyun yahi (comparison)

| Option | Cost | Always-on? | RAM | ffmpeg render | Setup | Verdict |
|---|---|---|---|---|---|---|
| **VPS (Hetzner CX22 / DO Bangalore)** | **₹350–550/mo** | ✅ | 2 GB | ✅ | 1 command | **✅ CHUNA** |
| Render free | ₹0 | ❌ 15 min idle pe sleep | 512 MB | ⚠️ tight, queue | git push | ❌ schedule miss |
| Render starter | $7 (~₹600) | ✅ | 512 MB | ⚠️ | git push | ⚠️ costly, RAM kam |
| Fly.io | ~$5 (~₹430) | ✅ | 1 GB | ✅ | CLI + volume | ⚠️ theek, jhanjhat |
| Oracle Always Free | ₹0 forever | ✅ | 24 GB | ✅ | signup + ARM | 🟡 backup option |
| Apna laptop | ₹0 | ❌ band hote hi ruk | — | ✅ | 5 min | ❌ automation nahi |

**Decision ka core:** schedule-based business hai. Server sota hai to reel nahi banti. Isliye
always-on + 1-2 GB RAM zaroori hai, aur ₹350 me wo milta hai. Free options me yahi ek compromise
karna padta hai — aur yahi compromise business todta hai.

---

## 15-minute runbook

### Step 1 — VPS lo (5 min)
Koi ek:
- **Hetzner CX22** — €3.79/mo (~₹350), best price/performance. Location: Singapore/Falkenstein (dashboard latency se farak nahi padta).
- **DigitalOcean** — Bangalore ($6/mo), India latency best.
- **Contabo** — Mumbai, ~₹450/mo, 4 GB RAM.

OS: **Ubuntu 24.04**. SSH key add karo. Root password login band rakho.

### Step 2 — Ek command (5 min)
```bash
ssh root@YOUR_SERVER_IP

# repo public hai:
git clone https://github.com/<you>/ai-influencer-os.git
cd ai-influencer-os
bash deploy/bootstrap.sh
```
Repo private / zip hai:
```bash
scp ai-influencer-deploy.zip root@YOUR_SERVER_IP:/root/
ssh root@YOUR_SERVER_IP
apt install -y unzip && unzip ai-influencer-deploy.zip && cd ai-influencer-os
bash deploy/bootstrap.sh
```

Script khud karta hai:
1. Docker install (+ ubuntu deps)
2. 2 GB swap (ffmpeg ke liye safety)
3. Firewall: 22, 8000, 80/443
4. App build + run: **strong 28-char password** generate, `./data` volume mount, `TZ=Asia/Kolkata`
5. Schedule seed: **build 07:00, 13:00, 19:00 IST** + publish slots
6. Cloudflare Tunnel → **public HTTPS URL** print

Output me aapko ye milega:
```
  Dashboard :  http://localhost:8000
  Public IP :  http://1.2.3.4:8000
  Password  :  Kf9x...28chars
  LIVE URL  :  https://random-words-here.trycloudflare.com
```

### Step 3 — Dashboard me 3 cheezein (5 min)
1. **Character tab** — aapka master face dikhna chahiye (yahi identity hai).
2. **Keys tab** — sirf `GEMINI_API_KEY` daalo (aistudio.google.com, free) → **Test connections** → Gemini `OK`.
   - Voice free hai (Edge TTS), kuch nahi chahiye.
   - IG / Fanvue / YouTube baad me, jab account ready ho.
3. **Dashboard tab** — "Generate now → 2" → 1-3 min me Reels tab me video aa jayegi. Ek baar dekh lo.

Bas. 07:00 IST se roz 3 reels khud banengi, 12:30/20:30 pe post hongi (IG keys daalne ke baad).

### Step 4 — Backup cron (1 min, ek baar)
```bash
crontab -e
# add:
30 2 * * * cd /root/ai-influencer-os && bash deploy/backup.sh >> logs/backup.log 2>&1
```
7 din ka backup `backup/` folder me rahega (~6 MB each).

---

## Permanent URL (Cloudflare Tunnel free)

`trycloudflare.com` URL temporary hota hai (container restart pe badal sakta hai). Permanent chahiye:

1. Cloudflare account → Zero Trust → **Tunnels** → Create tunnel → naam `influencer`.
2. Public hostname: `influencer.yourdomain.com` → service `http://localhost:8000`.
3. Token copy karo, phir:
```bash
docker rm -f influencer-tunnel
docker run -d --name influencer-tunnel --network host --restart unless-stopped \
  cloudflare/cloudflared:latest tunnel --no-autoupdate run --token <TOKEN>
```
Ab `https://influencer.yourdomain.com` permanent hai, free SSL ke saath. Domain ₹700/saal (Cloudflare/Namecheap).

Apna server + domain already hai? Caddy wala rasta simpler hai: `deploy/Caddyfile` copy karke reload — auto HTTPS.

---

## Kharcha (monthly)

| Item | Cost |
|---|---|
| VPS (Hetzner CX22) | ₹350 |
| Domain (optional) | ₹60 |
| Gemini image + script (free tier) | ₹0 |
| Edge TTS voice | ₹0 |
| ffmpeg + hosting + tunnel | ₹0 |
| fal.ai talking video (agar chahiye, ~₹15-25/reel × 90) | ₹1,400–2,200 |
| **TOTAL (bina fal)** | **₹350–410/mo** |
| **TOTAL (fal ke saath, best quality)** | **₹1,750–2,600/mo** |

Break-even: 1 Fanvue subscription (₹749) = server + domain cover.

---

## ₹0 chahiye? Oracle Always Free

4 ARM cores + 24 GB RAM, hamesha free. Friction: card verification + capacity.
```bash
# Oracle console -> Ampere A1 (4 OCPU, 24GB), Ubuntu 24.04 ARM
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
git clone <repo> && cd ai-influencer-os && bash deploy/deploy.sh --tunnel
```
Note: ARM image build hoga (Dockerfile arch-neutral hai), par Oracle kabhi kabhi A1 capacity nahi deta.

---

## Hardening checklist (public URL hai to zaroori)

- [ ] `ADMIN_PASSWORD` 20+ chars (script 28 deta hai) — `changeme` / `test` reject ho jata hai.
- [ ] Root password login band, sirf SSH key: `PasswordAuthentication no`
- [ ] `sudo apt install -y unattended-upgrades` (security patches auto)
- [ ] Port 8000 public na kholo — sirf tunnel use karo (`-p 127.0.0.1:8000:8000`)
- [ ] Weekly backup check: `ls -la backup/`
- [ ] `docker logs influencer-os | grep error` hafte me ek baar

---

## Monitoring (chhota par kaam ka)

```bash
# app zinda hai?
curl -fsS http://localhost:8000/health

# aaj kitni reels bani?
curl -s -b ck.txt http://localhost:8000/api/stats

# schedule IST me hai?
curl -s -b ck.txt http://localhost:8000/api/system
# -> {"timezone":"Asia/Kolkata","now":"...","builds_per_day":3}
```

Kuch fail hua to dashboard ke **Logs** tab me exact step dikh jayega (`script / image / voice / video / publish`).

---

## Ek line me

**Hetzner CX22 (₹350) + `bash deploy/bootstrap.sh` + Cloudflare Tunnel.**
15 minute, ek command, phir roz 3 reels apne aap.
