#!/usr/bin/env bash
# ============================================================================
#  FREE HOSTING — Google Cloud e2-micro (Always Free, 1 GB RAM)
#
#  GCP -> Compute Engine -> e2-micro, region: us-west1 / us-central1 / us-east1
#  Boot disk 30 GB standard. Ubuntu 24.04. Firewall: allow HTTP/HTTPS + tcp:8000.
#  SSH -> ye script:
#
#     curl -fsSL https://raw.githubusercontent.com/<you>/ai-influencer-os/main/deploy/free-gcp.sh | bash
#
#  Ye 1 GB box ke liye LOW_MEM=1 set karta hai: 720x1280 render + ultrafast preset +
#  2 GB swap. Quality theek rehti hai aur ffmpeg OOM nahi hota.
# ============================================================================
set -euo pipefail
log() { printf "\n\033[1;35m==> %s\033[0m\n" "$*"; }

log "Packages"
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl git unzip

log "Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi

log "2 GB swap (1 GB RAM ke liye zaroori)"
if ! swapon --show | grep -q '/swapfile'; then
  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

[ -f Dockerfile ] || { log "Repo folder me aao: git clone <repo> && cd ai-influencer-os"; exit 1; }

log "App deploy — LOW_MEM profile (720p)"
export TZ=Asia/Kolkata
export LOW_MEM=1
export FFMPEG_PRESET=ultrafast
export FFMPEG_CRF=26
export VIDEO_HEIGHT=1280
bash deploy/deploy.sh --tunnel

log "Backup cron"
(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo "30 2 * * * cd $(pwd) && bash deploy/backup.sh >> logs/backup.log 2>&1") | crontab -

log "DONE"
echo "Password: cat data/.admin_password"
echo "GCP firewall: VPC network -> Firewall -> allow tcp:8000 (ya tunnel URL use karo)."
