#!/usr/bin/env python3
"""05 — Publish the oldest queued reel (Instagram Reels + optionally YouTube Shorts).

Run it from cron at each posting slot. It publishes exactly one item per call,
so three crons a day = three posts a day.

  python src/05_publish.py                  # publish next queued item
  python src/05_publish.py --platform ig    # only Instagram
  python src/05_publish.py --dry-run
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, ROOT, character, dry_run, endpoints, ledger, save_ledger  # noqa: E402
from lib import providers  # noqa: E402

load_dotenv(ROOT / ".env")
IG = "https://graph.facebook.com"


# --------------------------------------------------------------------------- #
# Instagram Reels (Graph API)
# --------------------------------------------------------------------------- #
def ig_publish(video_path, caption, ep):
    user = os.getenv("IG_USER_ID")
    token = os.getenv("IG_ACCESS_TOKEN")
    ver = ep["publish"]["instagram_graph_version"]
    base = f"{IG}/{ver}"

    public_url = providers.upload_public(str(video_path))
    r = requests.post(f"{base}/{user}/media", data={
        "media_type": "REELS",
        "video_url": public_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": token,
    }, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"IG container: {r.status_code} {r.text[:300]}")
    creation_id = r.json()["id"]

    for _ in range(60):  # up to ~10 min of processing
        time.sleep(10)
        s = requests.get(f"{base}/{creation_id}", params={
            "fields": "status_code,status", "access_token": token}, timeout=60).json()
        code = s.get("status_code")
        print(f"    IG container -> {code}")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"IG processing error: {s}")
    else:
        raise RuntimeError("IG container never finished processing")

    p = requests.post(f"{base}/{user}/media_publish", data={
        "creation_id": creation_id, "access_token": token}, timeout=120)
    if p.status_code >= 400:
        raise RuntimeError(f"IG publish: {p.status_code} {p.text[:300]}")
    media_id = p.json()["id"]
    print(f"    IG published media id {media_id}")
    return media_id


# --------------------------------------------------------------------------- #
# YouTube Shorts
# --------------------------------------------------------------------------- #
def yt_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.getenv("YT_CLIENT_ID"),
        "client_secret": os.getenv("YT_CLIENT_SECRET"),
        "refresh_token": os.getenv("YT_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def yt_publish(video_path, title, description, tags, ep):
    token = yt_token()
    size = os.path.getsize(video_path)
    meta = {
        "snippet": {
            "title": (title[:95] + " #Shorts"),
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": ep["publish"].get("youtube_privacy", "public"),
            "selfDeclaredMadeForKids": False,
        },
    }
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos",
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(size),
            "X-Upload-Content-Type": "video/mp4",
        },
        json=meta, timeout=120)
    if init.status_code >= 400:
        raise RuntimeError(f"YT init: {init.status_code} {init.text[:300]}")
    url = init.headers["Location"]
    with open(video_path, "rb") as f:
        up = requests.put(url, data=f, headers={
            "Content-Type": "video/mp4", "Content-Length": str(size)}, timeout=1800)
    if up.status_code >= 400:
        raise RuntimeError(f"YT upload: {up.status_code} {up.text[:300]}")
    vid = up.json().get("id")
    print(f"    YT published video id {vid}")
    return vid


# --------------------------------------------------------------------------- #
def queued_items():
    items = []
    for p in OUT.rglob("item.json"):
        try:
            meta = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if meta.get("status") == "queued" and os.path.exists(meta.get("video", "")):
            items.append((meta["created"], p, meta))
    items.sort()
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=["ig", "yt", "both"], default="both")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true", help="show the caption, post nothing")
    args = ap.parse_args()
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"

    ch = character()
    ep = endpoints()
    items = queued_items()
    if not items:
        print("Queue empty — run src/02_generate_batch.py first.")
        return

    done = 0
    for created, path, meta in items[: args.limit]:
        tag = f"#{meta['ai_disclosure'].replace(' ', '')} #AIinfluencer"
        caption = f"{meta['caption_instagram']}\n\n{tag}"
        print(f"\nPublishing {meta['id']} ({created})")
        if dry_run():
            print(f"  [dry-run] caption:\n{caption}")
            continue

        results = {}
        if args.platform in ("ig", "both"):
            try:
                results["instagram"] = ig_publish(meta["video"], caption, ep)
            except Exception as e:  # noqa: BLE001
                print(f"  ! instagram failed: {e}")
                results["instagram_error"] = str(e)
        if args.platform in ("yt", "both") and os.getenv("YT_REFRESH_TOKEN"):
            try:
                results["youtube"] = yt_publish(
                    meta["video"], meta.get("caption_youtube", meta["hook"]),
                    caption, [meta["pillar"], "AIinfluencer", "shorts"], ep)
            except Exception as e:  # noqa: BLE001
                print(f"  ! youtube failed: {e}")
                results["youtube_error"] = str(e)

        if any(k for k in results if not k.endswith("_error")):
            meta["status"] = "published"
            done += 1
        else:
            meta["status"] = "failed"
        meta["published_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        meta["results"] = results
        Path(path).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        led = ledger()
        (led["failed"] if meta["status"] == "failed" else led["published"]).append(
            {"id": meta["id"], "at": meta["published_at"], "results": results})
        save_ledger(led)

    print(f"\n{done} published.")


if __name__ == "__main__":
    main()
