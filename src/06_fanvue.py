#!/usr/bin/env python3
"""06 — Fanvue: the PAID adult tier, fully automatable.

Why Fanvue and not OnlyFans (checked Oct 2026):
  * OnlyFans: AI content allowed ONLY if it "clearly features the verified Creator".
    A fictional AI girl cannot be an OF creator. Dead end. Do not waste a month on it.
  * Fanvue: fully-AI accounts are an official, verified category. AI label required.
    Creator keeps 80% (15% for the first 30 days). Real public API with OAuth 2.0.

Endpoints used (from api.fanvue.com/docs):
  GET    /users/me
  POST   /media/uploads                     -> mediaUuid + uploadId
  GET    /media/uploads/{uploadId}/parts/urls?from=1&to=N
  PUT    <signed url>   (raw bytes, capture ETag)
  PATCH  /media/uploads/{uploadId}          -> {parts:[{PartNumber,ETag}]}
  GET    /media/{uuid}                      -> poll until status=="ready"
  POST   /v1/posts                          -> text, mediaUuids, price(cents), publishAt
  POST   /v1/chats/mass-messages            -> mass DM (welcome / PPV drop)

Usage:
  python src/06_fanvue.py --check
  python src/06_fanvue.py --post --file out/x/final.mp4 --text "naya set 🖤" --price 699
  python src/06_fanvue.py --post --file out/x/final.mp4 --text "kal raat" --at 2026-10-28T22:00:00+05:30
  python src/06_fanvue.py --queue --price 699        # every queued item as a paid post
  python src/06_fanvue.py --mass --text "welcome 🖤"
  (add --dry-run to print payloads, call nothing)
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
from common import OUT, ROOT  # noqa: E402

load_dotenv(ROOT / ".env")

BASE = "https://api.fanvue.com"
API_VERSION = "2025-06-26"
TOKEN_URL = "https://auth.fanvue.com/oauth2/token"
DRY = False


# --------------------------------------------------------------------------- #
def _token():
    tok = os.getenv("FANVUE_ACCESS_TOKEN")
    if tok:
        return tok
    refresh = os.getenv("FANVUE_REFRESH_TOKEN")
    if not refresh:
        raise RuntimeError("Set FANVUE_ACCESS_TOKEN (or FANVUE_REFRESH_TOKEN + client id/secret) in .env")
    r = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": os.getenv("FANVUE_CLIENT_ID"),
        "client_secret": os.getenv("FANVUE_CLIENT_SECRET"),
    }, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Fanvue token refresh failed: {r.status_code} {r.text[:200]}")
    j = r.json()
    os.environ["FANVUE_ACCESS_TOKEN"] = j["access_token"]
    if j.get("refresh_token"):
        os.environ["FANVUE_REFRESH_TOKEN"] = j["refresh_token"]
    return j["access_token"]


def api(path, method="GET", body=None, params=None, raw=False, timeout=120):
    if DRY and method != "GET":
        print(f"  [dry-run] {method} {path}\n  body: {json.dumps(body, ensure_ascii=False)[:400]}")
        return {"dryRun": True}
    headers = {"Authorization": f"Bearer {_token()}", "X-Fanvue-API-Version": API_VERSION}
    if body is not None:
        headers["Content-Type"] = "application/json"
    url = f"{BASE}{path}"
    r = requests.request(method, url, headers=headers, params=params,
                         data=json.dumps(body) if body is not None else None, timeout=timeout)
    if raw:
        return r
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else {}


# --------------------------------------------------------------------------- #
# media upload (multipart, exactly as documented)
# --------------------------------------------------------------------------- #
def upload_media(path, media_type=None, name=None):
    p = Path(path)
    size = p.stat().st_size
    mt = media_type or ("video" if p.suffix.lower() in (".mp4", ".mov") else "image")
    name = name or p.stem
    print(f"  uploading {p.name} ({size/1024/1024:.1f} MiB, {mt})")
    sess = api("/media/uploads", "POST",
               {"name": name, "filename": p.name, "mediaType": mt, "sizeBytes": size})
    if DRY:
        return "00000000-0000-0000-0000-000000000000"

    upload_id, media_uuid = sess["uploadId"], sess["mediaUuid"]
    part_size = sess["partSize"]
    total = sess.get("totalParts") or (size + part_size - 1) // part_size
    signed = api(f"/media/uploads/{upload_id}/parts/urls", params={"from": 1, "to": total})
    parts = []
    offsets = {p_["partNumber"]: p_["url"] for p_ in signed["parts"]}
    with open(p, "rb") as f:
        for n in range(1, total + 1):
            chunk = f.read(part_size)
            put = requests.put(offsets[n], data=chunk, timeout=600)
            if put.status_code >= 400:
                raise RuntimeError(f"part {n} upload failed {put.status_code}")
            parts.append({"PartNumber": n, "ETag": put.headers.get("ETag", "")})
    api(f"/media/uploads/{upload_id}", "PATCH", {"parts": parts})

    for _ in range(120):
        time.sleep(2)
        m = api(f"/media/{media_uuid}")
        st = m.get("status")
        print(f"    media {media_uuid[:8]} -> {st}")
        if st == "ready":
            return media_uuid
        if st == "error":
            raise RuntimeError(f"media processing error: {m.get('errorReason')}")
    raise RuntimeError("media never became ready")


# --------------------------------------------------------------------------- #
def create_post(text, media_uuids, price_cents=None, audience="subscribers",
                publish_at=None, preview_uuid=None):
    body = {"text": text, "audience": audience, "mediaUuids": media_uuids}
    if price_cents:
        body["price"] = int(price_cents)
    if publish_at:
        body["publishAt"] = publish_at
    if preview_uuid:
        body["mediaPreviewUuid"] = preview_uuid
    out = api("/v1/posts", "POST", body)
    print(f"  post created: {out.get('uuid', '(dry-run)')}  price={price_cents}  at={publish_at or 'now'}")
    return out


def mass_message(text, media_uuid=None, idem=None):
    body = {"text": text}
    if media_uuid:
        body["mediaUuids"] = [media_uuid]
    headers_extra = {"Idempotency-Key": idem or f"mass-{int(time.time())}"}
    if DRY:
        print(f"  [dry-run] POST /v1/chats/mass-messages {json.dumps(body, ensure_ascii=False)[:300]}")
        return {"dryRun": True}
    r = requests.post(f"{BASE}/v1/chats/mass-messages", timeout=120,
                      headers={"Authorization": f"Bearer {_token()}",
                               "X-Fanvue-API-Version": API_VERSION,
                               "Content-Type": "application/json", **headers_extra},
                      data=json.dumps(body))
    if r.status_code >= 400:
        raise RuntimeError(f"mass message failed {r.status_code}: {r.text[:300]}")
    print("  mass message sent")
    return r.json()


# --------------------------------------------------------------------------- #
def queued():
    items = []
    for p in OUT.rglob("item.json"):
        try:
            m = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if m.get("status") == "queued" and os.path.exists(m.get("video", "")):
            items.append((m["created"], p, m))
    items.sort()
    return items


def main():
    global DRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify token, print account")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--queue", action="store_true", help="post every queued item to Fanvue")
    ap.add_argument("--mass", action="store_true")
    ap.add_argument("--file")
    ap.add_argument("--text", default="")
    ap.add_argument("--price", type=int, default=None, help="cents; 699 = $6.99 (min 300)")
    ap.add_argument("--at", default=None, help="ISO publishAt, e.g. 2026-10-28T22:00:00+05:30")
    ap.add_argument("--audience", default="subscribers",
                    choices=["subscribers", "followers-and-subscribers"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    DRY = args.dry_run

    if args.check:
        me = api("/users/me")
        print(json.dumps(me, indent=2)[:800])
        return

    if args.mass:
        mass_message(args.text or "Welcome 🖤")
        return

    if args.queue:
        items = queued()
        if not items:
            print("queue empty")
            return
        for _created, _path, meta in items:
            uid = upload_media(meta["video"], "video")
            create_post(meta.get("caption_instagram", meta.get("hook", "")),
                        [uid], price_cents=args.price or 699,
                        audience=args.audience, publish_at=None)
            meta["status"] = "published_fanvue"
            Path(_path).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    if args.post:
        if not args.file:
            raise SystemExit("--post needs --file")
        uid = upload_media(args.file)
        create_post(args.text, [uid], price_cents=args.price,
                    audience=args.audience, publish_at=args.at)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
