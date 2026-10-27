#!/usr/bin/env bash
# Instant public HTTPS URL — bina domain, bina DNS, bina SSL setup.
# Cloudflare "quick tunnel" use hota hai. URL temporary hota hai (container jitna jeeta hai).
#
#   bash deploy/cloudflared.sh            -> https://random-words.trycloudflare.com
#   bash deploy/cloudflared.sh stop       -> tunnel band
#
# Permanent URL chahiye to Cloudflare account me named tunnel banao (docs/website_deploy.md).
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"
NAME="${NAME:-influencer-tunnel}"

if [ "${1:-}" = "stop" ]; then
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  echo "tunnel stopped"
  exit 0
fi

curl -fsS -m 5 "http://localhost:${PORT}/health" >/dev/null 2>&1 \
  || { echo "App ${PORT} pe nahi chal raha — pehle: bash deploy/deploy.sh"; exit 1; }

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --network host --restart unless-stopped \
  cloudflare/cloudflared:latest tunnel --no-autoupdate --url "http://localhost:${PORT}" >/dev/null

echo -n "URL ban raha hai"
URL=""
for i in $(seq 1 30); do
  URL="$(docker logs "$NAME" 2>&1 | grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1 || true)"
  [ -n "$URL" ] && break
  echo -n "."; sleep 2
done
echo
if [ -z "$URL" ]; then
  echo "URL nahi mila. Logs dekho: docker logs $NAME"
  exit 1
fi
echo "=============================================="
echo "  LIVE URL :  $URL"
echo "  Password :  $(cat data/.admin_password 2>/dev/null || echo '<.env me ADMIN_PASSWORD>')"
echo "=============================================="
