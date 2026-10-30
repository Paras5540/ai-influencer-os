#!/usr/bin/env python3
"""Upload flow — aap video daalo, ye usme aapki ladki ka character swap karta hai.

  assets/uploads/ me .mp4 daalo (GitHub web se drag-drop bhi chalega)
  -> scripts/swap_upload.py
  -> assets/uploads/done/ me move
  -> out/<reel>/ final.mp4 + thumb
  -> content/ (website gallery)
  -> POST tabhi jab aap kahen: Actions -> pipeline -> task=instagram

FAL_KEY na ho to kuch nahi karta, saaf message deta hai (crash nahi).
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

UPLOADS = ROOT / "assets" / "uploads"
DONE = UPLOADS / "done"
STATE = ROOT / "state" / "uploads.json"
MAX_SEC = 10  # motion model limit


def ledger():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:  # noqa: BLE001
            return {"done": []}
    return {"done": []}


def save(l):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(l, ensure_ascii=False, indent=2))


def main():
    from lib import media
    import motion

    UPLOADS.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)

    vids = [p for p in sorted(UPLOADS.glob("*.mp4")) if p.stat().st_size > 100_000]
    if not vids:
        print("assets/uploads me koi video nahi — kuch karne ko nahi")
        return 0

    if not os.getenv("FAL_KEY"):
        print(f"{len(vids)} video mili par FAL_KEY missing — swap nahi ho sakta.")
        print("  FAL key: fal.ai/dashboard/keys  -> .env ya Actions secret")
        print("  Videos waise hi rakhi hain, key aate hi ye khud chal jayengi.")
        return 0

    shots = sorted((ROOT / "assets" / "shots").glob("shot_*.png"))
    if not shots:
        print("assets/shots khaali — character face nahi mila")
        return 0

    ep = json.loads((ROOT / "config" / "endpoints.json").read_text(encoding="utf-8"))
    l = ledger()
    made = 0

    for vid in vids:
        if vid.name in l["done"]:
            continue
        dur = media.duration(str(vid))
        if dur > MAX_SEC:
            trimmed = vid.with_name(f"{vid.stem}_trim.mp4")
            media.run(["ffmpeg", "-y", "-i", str(vid), "-t", str(MAX_SEC),
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                       "-an", "-pix_fmt", "yuv420p", str(trimmed)])
            src = trimmed
            print(f"{vid.name}: {dur:.1f}s -> {MAX_SEC}s trim")
        else:
            src = vid

        shot = shots[made % len(shots)]
        hook = f"{vid.stem.replace('_', ' ').upper()[:22]}" or "NEW DROP"
        caption = (f"{vid.stem.replace('_', ' ')}\n\n"
                   "#reels #trending #dance #mumbai #aigeneratedcharacter")
        print(f"swap: {vid.name} + {shot.name}")
        try:
            raw = motion.fal_motion(shot, src, ep)
            motion.finish(raw, hook, caption)
            made += 1
            l["done"].append(vid.name)
            shutil.move(str(vid), str(DONE / vid.name))
        except Exception as e:  # noqa: BLE001
            print(f"  ! fail ({str(e)[:160]}) — video wahin rakhi hai, dobara try hoga")

    save(l)
    print(f"swap done: {made}/{len(vids)}")
    return made


if __name__ == "__main__":
    main()
