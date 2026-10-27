#!/usr/bin/env bash
# ============================================================================
#  One-command deploy: Docker + strong password + data volume + IST + 3 reels/day
#
#  Chalao:  bash deploy/deploy.sh
#  Roke:    docker rm -f influencer-os
#  Log:     docker logs -f influencer-os
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
TUNNEL=0
for a in "$@"; do [ "$a" = "--tunnel" ] && TUNNEL=1; done
NAME="${NAME:-influencer-os}"
DATA_DIR="${DATA_DIR:-$PWD/data}"

command -v docker >/dev/null 2>&1 || { echo "Docker nahi mila — pehle Docker install karo: https://docs.docker.com/engine/install/"; exit 1; }

mkdir -p "$DATA_DIR"

# ---------- 1. strong password (auto-generate, save locally) ----------
PW_FILE="$DATA_DIR/.admin_password"
if [ -n "${ADMIN_PASSWORD:-}" ]; then
  PW="$ADMIN_PASSWORD"
elif [ -f "$PW_FILE" ]; then
  PW="$(cat "$PW_FILE")"
else
  PW="$(head -c 32 /dev/urandom | base64 | tr -d '/+=\n' | cut -c1-28)"
  printf '%s' "$PW" > "$PW_FILE"
  chmod 600 "$PW_FILE" 2>/dev/null || true
fi
case "$PW" in
  changeme|test|admin|password) echo "ADMIN_PASSWORD bahut kamzor hai — badal do."; exit 1;;
esac

# ---------- 2. build ----------
echo "==> building image (pehli baar 2-4 min lagta hai) ..."
docker build -t influencer-os:latest .

# ---------- 3. (re)start with volume + IST ----------
echo "==> starting container ..."
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" \
  --restart unless-stopped \
  -p "${PORT}:8000" \
  -e TZ=Asia/Kolkata \
  -e ADMIN_PASSWORD="$PW" \
  -v "${DATA_DIR}:/app/data" \
  influencer-os:latest >/dev/null

# ---------- 4. wait until healthy ----------
echo -n "==> waiting for health"
for i in $(seq 1 40); do
  if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; then echo " ok"; break; fi
  echo -n "."; sleep 2
  [ "$i" = "40" ] && { echo; echo "Health check fail — logs dekho: docker logs $NAME"; exit 1; }
done

# ---------- 5. seed schedule (3 builds/day, IST) ----------
python3 - "$PORT" <<'PY' || true
import json,sys,urllib.request,http.cookiejar,os
port=sys.argv[1]; pw=open('data/.admin_password').read().strip() if os.path.exists('data/.admin_password') else os.environ.get('ADMIN_PASSWORD','')
base=f"http://localhost:{port}"
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
req=urllib.request.Request(base+"/api/login",data=json.dumps({"password":pw}).encode(),headers={"Content-Type":"application/json"})
op.open(req).read()
rows=json.loads(op.open(base+"/api/schedule").read())
print("schedule:")
for r in rows: print(f"  {r['task']:8s} {r['at']}  {'on' if r['enabled'] else 'off'}")
PY

# ---------- 6. URL ----------
IP="$(curl -fsS -m 4 https://api.ipify.org 2>/dev/null || echo '')"
echo
echo "=============================================================="
echo "  Dashboard :  http://localhost:${PORT}"
[ -n "$IP" ] && echo "  Public IP :  http://${IP}:${PORT}   (firewall me port ${PORT} kholna padega)"
echo "  Password  :  ${PW}"
echo "  Saved at  :  ${DATA_DIR}/.admin_password"
echo "  Schedule  :  build 07:00, 13:00, 19:00 IST  (3 reels/day)"
echo "               fanvue 09:00, 22:00 · ig 12:30, 20:30"
echo "  Logs      :  docker logs -f ${NAME}"
echo "=============================================================="
echo
if [ "$TUNNEL" = "1" ]; then
  bash deploy/cloudflared.sh
else
  echo "HTTPS URL chahiye (bina domain)?  bash deploy/cloudflared.sh"
fi
