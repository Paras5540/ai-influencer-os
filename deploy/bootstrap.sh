#!/usr/bin/env bash
# ============================================================================
#  ONE-LINE INSTALLER for a fresh Ubuntu 22.04/24.04 VPS.
#
#  Naya VPS lo -> SSH karo -> ye ek line paste karo:
#
#     curl -fsSL https://raw.githubusercontent.com/<you>/ai-influencer-os/main/deploy/bootstrap.sh | bash
#
#  Repo private hai? To zip upload karke:
#     unzip ai-influencer-deploy.zip && cd ai-influencer-os && bash deploy/bootstrap.sh
#
#  Kya karta hai:
#    1. system update + Docker install
#    2. swap on (2GB RAM pe ffmpeg ke liye safety)
#    3. firewall: 22 + 8000 (+ 80/443 agar domain baad me)
#    4. deploy.sh chala ke app start + schedule seed
#    5. Cloudflare Tunnel se public HTTPS URL
# ============================================================================
set -euo pipefail

log() { printf "\n\033[1;35m==> %s\033[0m\n" "$*"; }
cd "$(dirname "$0")/.." 2>/dev/null || true
if [ ! -f Dockerfile ]; then
  echo "Repo root me nahi ho. 'cd ai-influencer-os' karke phir chalao."; exit 1
fi

# ---------- 1. docker ----------
if ! command -v docker >/dev/null 2>&1; then
  log "Docker install ho raha hai"
  sudo apt-get update -qq
  sudo apt-get install -y -qq ca-certificates curl gnupg git unzip
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
fi
log "Docker: $(docker --version)"

# ---------- 2. swap (ffmpeg render ke liye) ----------
if ! swapon --show | grep -q '/swapfile'; then
  log "2GB swap on"
  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

# ---------- 3. firewall ----------
if command -v ufw >/dev/null 2>&1; then
  log "Firewall (22 + 8000)"
  sudo ufw allow OpenSSH >/dev/null 2>&1 || sudo ufw allow 22/tcp >/dev/null 2>&1 || true
  sudo ufw allow 8000/tcp >/dev/null 2>&1 || true
  sudo ufw allow 80,443/tcp >/dev/null 2>&1 || true
  sudo ufw --force enable >/dev/null 2>&1 || true
fi

# ---------- 4. app ----------
log "App deploy"
export TZ=Asia/Kolkata
bash deploy/deploy.sh

# ---------- 5. public HTTPS URL ----------
log "Public HTTPS URL (Cloudflare Tunnel)"
bash deploy/cloudflared.sh || echo "Tunnel skip — port 8000 se direct access kar sakte ho."

log "DONE"
echo "Dashboard: upar wala URL / http://SERVER-IP:8000"
echo "Password : cat data/.admin_password"
