#!/usr/bin/env python3
"""Montage reel builder — dance/trend style, koi talking head nahi.

Ek reel = 6-8 face-locked shots, ~1.1s each, hard cuts on beat, hook text overlay,
background music. Sab ffmpeg se — koi video API nahi chahiye (100% free).

  python scripts/montage.py --count 1
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "assets" / "shots"
MUSIC = ROOT / "assets" / "music"
OUT = ROOT / "out"
W, H = 1080, 1920
SHOT_SEC = float(os.getenv("SHOT_SEC", "1.9"))
TARGET_SEC = float(os.getenv("TARGET_SEC", "30"))

CAPTIONS = [
    ("3 OUTFITS, EK DIN", "Save kar lo. Kaunsa best laga? 👇\n\n"
     "#outfitideas #indianfashion #mumbai #grwm #reels #aigeneratedcharacter"),
    ("DESI GIRL SUMMER", "Saree se street style tak — sab ek hi din me.\n\n"
     "#desigirl #summerlook #indianwear #fashionreels #aigeneratedcharacter"),
    ("EK SHOT MEIN", "Batao konsa look sabse zyada pasand aaya?\n\n"
     "#transition #outfittransition #mumbai #grwm #aigeneratedcharacter"),
    ("GYM SE PARTY", "Same girl, do moods. Save kar lo.\n\n"
     "#gymtok #nightout #indiancreator #fitness #aigeneratedcharacter"),
    ("CAFE DIARIES", "Bandra wali shaam, ek acchi coffee.\n\n"
     "#cafevibes #mumbai #bandra #aesthetic #aigeneratedcharacter"),
    ("NIGHT OUT", "Kaali dress, halki smile. Bas.\n\n"
     "#nightout #blackdress #mumbai #partylook #aigeneratedcharacter"),
]

CAPTIONS_BY_TAG = {
    "dance":   ("", "Save kar lo, sound on 🔊\n\n#dance #trending #reels #mumbai #aigeneratedcharacter"),
    "desi":    ("", "Saree kinda evening 🖤\n\n#desigirl #sareelove #indianwear #reels #aigeneratedcharacter"),
    "gym":     ("", "Gym se glow tak 💪\n\n#gymtok #fitness #indiancreator #reels #aigeneratedcharacter"),
    "night":   ("", "Kaali dress, halki smile.\n\n#nightout #partylook #mumbai #reels #aigeneratedcharacter"),
    "cafe":    ("", "Bandra wali shaam ☕\n\n#cafevibes #mumbai #bandra #aesthetic #aigeneratedcharacter"),
    "beach":   ("", "Goa state of mind 🌊\n\n#beachvibes #goa #summerlook #reels #aigeneratedcharacter"),
    "street":  ("", "Street style, ek shirt, teen look.\n\n#streetstyle #outfitideas #mumbai #aigeneratedcharacter"),
    "fashion": ("", "Ek din, teen look 👗\n\n#grwm #outfitideas #indianfashion #reels #aigeneratedcharacter"),
}

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Noto Sans Devanagari,104,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,-1,0,0,0,100,100,1,0,1,7,4,8,80,80,180,1
Style: Cta,Noto Sans Devanagari,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,190,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(sec):
    h, m, s = int(sec // 3600), int(sec % 3600 // 60), sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def run(cmd, quiet=True):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd[:8])}\n{p.stderr[-800:]}")
    if not quiet:
        print(" ".join(cmd[:8]))
    return p


def shots():
    files = sorted(p for p in SHOTS.glob("*.png"))
    if not files:
        files = sorted(p for p in SHOTS.glob("*.jpg"))
    return files


def pick(n, day_seed):
    pool = shots()
    if not pool:
        raise RuntimeError(f"no shots in {SHOTS} — assets/shots me images daalo")
    rnd = random.Random(day_seed)
    pool = pool[:]           # copy
    rnd.shuffle(pool)
    out = []
    while len(out) < n:
        out += pool
    return out[:n]


def clip(shot, idx, out_path):
    """1 shot -> 1.1s vertical clip with slow zoom (in/out alternate)."""
    frames = int(SHOT_SEC * 30)
    zoom_in = (idx % 2 == 0)
    if zoom_in:
        z = "min(1.00+%.5f*on,1.08)" % (0.08 / frames)
    else:
        z = "max(1.08-%.5f*on,1.00)" % (0.08 / frames)
    vf = (f"scale={int(W*1.35)}:{int(H*1.35)}:force_original_aspect_ratio=increase,"
          f"crop={int(W*1.35)}:{int(H*1.35)},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.28':"
          f"d={frames}:s={W}x{H}:fps=30,setsar=1")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(shot), "-t", f"{SHOT_SEC:.2f}",
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", str(out_path)])


def ass(hook, total):
    lines = [ASS_HEADER]
    lines.append(f"Dialogue: 1,{ts(0)},{ts(min(2.4, total))},Hook,,0,0,0,,"
                 f"{{\\fad(120,200)}}{hook}\n")
    lines.append(f"Dialogue: 0,{ts(max(0, total-2.6))},{ts(total)},Cta,,0,0,0,,"
                 f"{{\\fad(150,150)}}SAVE KAR LO\n")
    return "".join(lines)


def manifest():
    p = SHOTS / "manifest.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def hook_for(shot):
    m = manifest().get(Path(shot).name)
    return m["hook"] if m else "NEW DROP"


def pick_music():
    tracks = sorted(MUSIC.glob("*.m4a")) + sorted(MUSIC.glob("*.mp3")) + sorted(MUSIC.glob("*.wav"))
    return random.choice(tracks) if tracks else None


def build(count=1, hooks=None):
    OUT.mkdir(parents=True, exist_ok=True)
    day = int(time.time() // 86400)
    for k in range(count):
        n_shots = max(6, int(round(TARGET_SEC / SHOT_SEC)))
        chosen = pick(n_shots, day * 10 + k)
        hook = (hooks[(k % len(hooks))] if hooks else hook_for(chosen[0]))
        tag = (manifest().get(Path(chosen[0]).name) or {}).get("tag", "fashion")
        caption = CAPTIONS_BY_TAG.get(tag, CAPTIONS[(day + k) % len(CAPTIONS)])
        total = round(n_shots * SHOT_SEC, 2)
        name = f"{datetime.now().strftime('%Y-%m-%d')}-montage-{datetime.now().strftime('%H%M%S')}"
        wd = OUT / name
        wd.mkdir(parents=True, exist_ok=True)

        parts = []
        for i, shot in enumerate(chosen):
            p = wd / f"p{i:02d}.mp4"
            clip(shot, i + k, p)
            parts.append(p)

        lst = wd / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        base = wd / "video.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", str(base)])

        a = wd / "hook.ass"
        a.write_text(ass(hook, total), encoding="utf-8")

        music = pick_music()
        final = wd / "final.mp4"
        cmd = ["ffmpeg", "-y", "-i", str(base)]
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            cmd += ["-filter_complex",
                    f"[0:v]ass={a}[v];[1:a]volume=0.55,afade=t=in:st=0:d=0.6[a]",
                    "-map", "[v]", "-map", "[a]"]
        else:
            cmd += ["-vf", f"ass={a}", "-map", "0:v"]
        cmd += ["-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-pix_fmt", "yuv420p", "-r", "30"]
        if music:
            cmd += ["-c:a", "aac", "-b:a", "160k", "-shortest"]
        cmd += [str(final)]
        run(cmd)

        thumb = wd / "thumb.jpg"
        run(["ffmpeg", "-y", "-ss", "0.4", "-i", str(final), "-frames:v", "1",
             "-q:v", "3", str(thumb)])

        meta = {
            "id": name,
            "created": datetime.now().isoformat(),
            "video": str(final),
            "hook": hook.title(),
            "topic": hook.title(),
            "pillar": "glam_looks",
            "caption_instagram": caption,
            "caption_youtube": hook.title(),
            "status": "ready",
            "ai_disclosure": "AI-generated character",
        }
        (wd / "item.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        for p in parts + [lst, base]:
            try:
                p.unlink()
            except OSError:
                pass
        print(f"montage ready: {name} ({n_shots} shots, {total}s)")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--hook", action="append", help="custom hook (repeatable)")
    a = ap.parse_args()
    build(a.count, a.hook)
