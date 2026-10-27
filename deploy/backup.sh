#!/usr/bin/env bash
# Daily backup of data/ (SQLite + reels + thumbnails). 7 copies rakhta hai.
#
# Install (ek baar):
#   (crontab -l 2>/dev/null; echo "30 2 * * * cd $(pwd) && bash deploy/backup.sh >> logs/backup.log 2>&1") | crontab -
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backup logs
STAMP="$(TZ=Asia/Kolkata date +%Y%m%d-%H%M)"
tar -czf "backup/influencer-$STAMP.tar.gz" data 2>/dev/null
ls -1t backup/influencer-*.tar.gz | tail -n +8 | xargs -r rm -f
echo "[$STAMP] backup ok: $(du -h "backup/influencer-$STAMP.tar.gz" | cut -f1) | kept: $(ls -1 backup/*.tar.gz | wc -l)"
