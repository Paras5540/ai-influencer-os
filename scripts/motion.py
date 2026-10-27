#!/usr/bin/env python3
"""Motion transfer (character swap) — apna character, kisi aur ki MOTION.

  python scripts/motion.py --ref assets/motion/clip.mp4 --shot assets/shots/shot_02.png

Reference video SIRF licensed/CC0 hona chahiye (Pexels / Pixabay / Coverr free license —
modification + commercial use allowed). Kisi influencer ki Instagram reel use karna
deepfake + copyright hai: platform ban + legal risk. Wo raasta is tool me jaan-boojh ke
block kiya gaya hai (source domain allowlist).

Flow: reference clip + character image -> fal motion model -> 1080x1920 + hook + music
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lib import media  # noqa: E402
import montage  # noqa: E402

ALLOWED_HOSTS = ("pexels.com", "pixabay.com", "coverr.co", "mixkit.co", "cdn.coverr.co",
                 "videos.pexels.com", "cdn.pixabay.com")


def check_source(ref: Path, source_url: str = ""):
    """Licensed source hi chalega. Instagram/TikTok se download = block."""
    name = (source_url or str(ref)).lower()
    if any(b in name for b in ("instagram", "tiktok", "instagr.am", "youtube", "shorts")):
        raise SystemExit(
            "❌ Ye source allowed nahi (Instagram/TikTok/YouTube).\n"
            "   Deepfake + copyright = account ban + legal case.\n"
            "   Licensed clip lo: pexels.com/search/videos/dance/ (free, commercial ok)\n"
            "   Phir: python scripts/motion.py --ref assets/motion/clip.mp4 --source pexels.com")
    if source_url and not any(h in name for h in ALLOWED_HOSTS):
        raise SystemExit(f"❌ Source host allowed nahi: {source_url}\n   Allowed: {', '.join(ALLOWED_HOSTS)}")


def fal_motion(shot: Path, ref: Path, ep):
    from lib import providers
    key = os.getenv("FAL_KEY")
    if not key:
        raise SystemExit(
            "FAL_KEY nahi hai. 2 raste:\n"
            "  1) fal.ai se key lo (₹15-40 per reel) -> .env me FAL_KEY\n"
            "  2) Free manual: kling.ai ya higgsfield.ai (daily free credits) me\n"
            "     apni shot + licensed clip daalo, output download karke\n"
            "     assets/motion/ me rakho, phir: python scripts/motion.py --local <file>")
    os.environ["FAL_KEY"] = key
    m = ep.get("motion", {})
    endpoint = m.get("endpoint", "fal-ai/kling-video/v1.6/pro/motion-control")
    img_url = providers.upload_public(str(shot))
    vid_url = providers.upload_public(str(ref))
    payload = {
        "image_url": img_url,
        "video_url": vid_url,
        "character_orientation": "video",
        "mode": "720p",
        "prompt": "same person as the image, performing the exact motion of the reference video, "
                  "natural body physics, photorealistic, no text",
    }
    print(f"  fal: {endpoint}")
    out = providers.fal_run(endpoint, payload)
    url = None
    for k in ("video", "video_url", "url", "output"):
        v = out.get(k) if isinstance(out, dict) else None
        if isinstance(v, dict):
            v = v.get("url")
        if isinstance(v, str) and v.startswith("http"):
            url = v
            break
    if not url:
        raise SystemExit(f"no video url in response: {json.dumps(out)[:300]}")
    tmp = ROOT / "out" / f"motion_raw_{int(time.time())}.mp4"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    providers.download(url, tmp)
    return tmp


def finish(raw: Path, hook: str, caption: str):
    name = f"{time.strftime('%Y-%m-%d')}-motion-{time.strftime('%H%M%S')}"
    wd = ROOT / "out" / name
    wd.mkdir(parents=True, exist_ok=True)
    dur = min(media.duration(str(raw)), 15.0)
    ass = wd / "hook.ass"
    ass.write_text(montage.ass(hook, dur), encoding="utf-8")
    music = montage.pick_music()
    final = wd / "final.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(raw)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music),
                "-filter_complex",
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"ass={ass}[v];[1:a]volume=0.5,afade=t=in:st=0:d=0.5[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={ass}",
                "-map", "0:v"]
    cmd += ["-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", "30", str(final)]
    media.run(cmd)
    thumb = wd / "thumb.jpg"
    media.run(["ffmpeg", "-y", "-ss", "0.5", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(thumb)])
    meta = {"id": name, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "video": str(final),
            "hook": hook.title(), "topic": hook.title(), "pillar": "motion",
            "caption_instagram": caption, "caption_youtube": hook.title(),
            "status": "ready", "ai_disclosure": "AI-generated character"}
    (wd / "item.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"motion reel ready: {name} ({dur:.1f}s)")
    return wd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", help="licensed reference clip (mp4)")
    ap.add_argument("--shot", default="assets/shots/shot_02.png", help="character image")
    ap.add_argument("--source", default="", help="clip ka source URL (allowlist check)")
    ap.add_argument("--local", help="already-generated motion video (free manual path)")
    ap.add_argument("--hook", default="SHE CAN MOVE")
    ap.add_argument("--caption", default="Movement > words. Sound on 🔊\n\n#dance #reels #trending #aigeneratedcharacter")
    a = ap.parse_args()

    ep = json.loads((ROOT / "config" / "endpoints.json").read_text(encoding="utf-8"))

    if a.local:
        raw = Path(a.local)
        if not raw.exists():
            raise SystemExit(f"file nahi mila: {raw}")
    else:
        if not a.ref:
            raise SystemExit("--ref (licensed clip) ya --local (ready video) do")
        ref = Path(a.ref)
        if not ref.exists():
            raise SystemExit(f"clip nahi mila: {ref}  (pexels.com se free download karo)")
        check_source(ref, a.source)
        raw = fal_motion(Path(a.shot), ref, ep)

    finish(raw, a.hook, a.caption)


if __name__ == "__main__":
    main()
