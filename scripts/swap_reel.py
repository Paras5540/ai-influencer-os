#!/usr/bin/env python3
"""Swap reel — asli video ka motion, apni ladki ka chehra.

Reference video: assets/motion/ me jo licensed clip rakhi hai (Mixkit/Pexels).
Aap apni koi video bhi wahin daal sakte ho (jo aapki ho ya licensed ho).

  python scripts/swap_reel.py --auto --count 2      # CI/schedule isse chalata hai
  python scripts/swap_reel.py --local file.mp4      # manual output (Kling/Higgsfield free se)

FAL_KEY na ho to ye script fail nahi karti — clean message ke saath skip karti hai.
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import montage  # noqa: E402
import motion  # noqa: E402

MOTION = ROOT / "assets" / "motion"

HOOKS = {
    "dance_01": ("SHE CAN MOVE", "Movement > words. Sound on 🔊\n\n#dance #trending #reels #mumbai #aigeneratedcharacter"),
    "dance_02": ("WATCH HER", "Ye move dekha? 💃\n\n#dance #viral #reels #explore #aigeneratedcharacter"),
    "dance_03": ("NACH LE", "Bas camera on kiya 🖤\n\n#desigirl #dance #reels #trending #aigeneratedcharacter"),
}
DEFAULT_HOOK = ("TREND ALERT", "New drop 🔥\n\n#trending #reels #viral #aigeneratedcharacter")


def clips():
    return sorted(p for p in MOTION.glob("*.mp4") if p.stat().st_size > 200_000)


def shots():
    return sorted((ROOT / "assets" / "shots").glob("shot_*.png"))


def run(count=1):
    if not os.getenv("FAL_KEY"):
        print("SKIP motion: FAL_KEY missing (real character swap ke liye zaroori hai).")
        print("      Free manual: kling.ai / higgsfield.ai -> output assets/motion/ -> "
              "python scripts/swap_reel.py --local <file>")
        return 0
    cl, sh = clips(), shots()
    if not cl or not sh:
        print("SKIP: assets/motion ya assets/shots khaali hai")
        return 0

    ep = json.loads((ROOT / "config" / "endpoints.json").read_text(encoding="utf-8"))
    made = 0
    for i in range(count):
        clip = random.choice(cl)
        shot = random.choice(sh)
        hook, caption = HOOKS.get(clip.stem, DEFAULT_HOOK)
        try:
            raw = motion.fal_motion(shot, clip, ep)
            motion.finish(raw, hook, caption)
            made += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ! swap failed ({str(e)[:140]})")
    print(f"motion reels built: {made}/{count}")
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--local", help="ready video (free manual swap output)")
    ap.add_argument("--hook", default=None)
    ap.add_argument("--caption", default=None)
    a = ap.parse_args()

    if a.local:
        hook, caption = HOOKS.get(Path(a.local).stem, DEFAULT_HOOK)
        motion.finish(Path(a.local), a.hook or hook, a.caption or caption)
    else:
        run(a.count)
