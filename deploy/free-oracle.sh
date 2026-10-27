#!/usr/bin/env bash
# ============================================================================
#  FREE HOSTING — Oracle Cloud "Always Free" (₹0 forever, 24 GB RAM, no sleep)
#
#  Oracle Cloud -> Compute -> Instance -> Ampere A1 (4 OCPU / 24 GB), Ubuntu 24.04 ARM
#  SSH karke ye script chalao:
#
#     curl -fsSL https://raw.githubusercontent.com/<you>/ai-influencer-os/main/deploy/free-oracle.sh | bash
#
#  Repo private/zip:
#     unzip ai-influencer-deploy.zip && cd ai-influencer-os && bash deploy/free-oracle.sh
#
#  Kyun Oracle: sota nahi (Render free 15 min pe so jata hai), 24 GB RAM (ffmpeg khush),
#  200 GB disk free, aur hamesha ke liye free. Card verification lagti hai (₹1 hold).
# ============================================================================
set -euo pipefail

log() { printf "\n\033[1;35m==> %s\033[0m\n" "$*"; }

log "System update"
sudo apt-get update -qq && sudo apt-get install -y -qq ca-certificates curl git unzip

log "Docker install (ARM64)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
fi
docker --version

log "iptables (Oracle ka default firewall) — 8000 khol rahe hain"
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || true

if [ ! -f Dockerfile ]; then
  log "Repo folder me aao: git clone <your-repo> && cd ai-influencer-os"
  exit 1
fi

log "App deploy (password + volume + IST + 3 reels/day)"
export TZ=Asia/Kolkata
bash deploy/deploy.sh --tunnel

log "Backup cron"
(crontab -l 2>/dev/null | grep -v 'backup.sh'; echo "30 2 * * * cd $(pwd) && bash deploy/backup.sh >> logs/backup.log 2>&1") | crontab -

log "DONE — Oracle dashboard me 'Always Free' instance chal raha hai. Bill ₹0."
echo "Password: cat data/.admin_password"
echo "Note: Oracle console -> VCN -> Security List me bhi port 8000 allow karna (agar direct IP use karna ho)."
