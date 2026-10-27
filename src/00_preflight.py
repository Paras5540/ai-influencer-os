#!/usr/bin/env python3
"""00 — Preflight. Tells you exactly what is missing before a run costs you money."""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv  # noqa: E402

from common import ASSETS, ROOT, character, endpoints  # noqa: E402

load_dotenv(ROOT / ".env")

OK, BAD = "\033[92mOK\033[0m", "\033[91mMISSING\033[0m"
rows = []


def check(label, cond, hint=""):
    rows.append((label, bool(cond), hint))


check("ffmpeg", shutil.which("ffmpeg"))
check("ffprobe", shutil.which("ffprobe"))
check("python3.9+", sys.version_info >= (3, 9))

for v in ("GEMINI_API_KEY",):
    check(v, os.getenv(v), "image + script (free tier ok)")
check("FANVUE_ACCESS_TOKEN", os.getenv("FANVUE_ACCESS_TOKEN"),
      "premium tier only — src/06_fanvue.py")
try:
    import edge_tts  # noqa: F401
    check("edge-tts installed (free voice)", True)
except ImportError:
    check("edge-tts installed (free voice)", False, "pip install edge-tts")
for v in ("IG_USER_ID", "IG_ACCESS_TOKEN"):
    check(v, os.getenv(v), "Instagram publish step only")
for v in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"):
    check(v, os.getenv(v), "YouTube Shorts step only (optional)")

ep0 = endpoints()
ch = character()
if ep0.get("tts", {}).get("provider") == "edge":
    check("voice: edge-tts (free, no key)", True)
else:
    vid = ch["voice"].get("elevenlabs_voice_id", "")
    check("character voice_id configured", not str(vid).startswith("REPLACE"))
from common import character_dir  # noqa: E402
check("master face image", (character_dir() / "master.png").exists(),
      "run: python src/01_build_character.py --config <cfg> --dir <dir>")

# Devanagari font for burned captions
fonts = []
for root in ("/usr/share/fonts", os.path.expanduser("~/.fonts"), "/Library/Fonts"):
    if os.path.isdir(root):
        for dirpath, _d, files in os.walk(root):
            fonts += [f for f in files if "devanagari" in f.lower() or f.lower().startswith("noto")]
check("Devanagari font installed", any("devanagari" in f.lower() for f in fonts),
      "apt install fonts-noto-devanagari  (captions render as boxes without it)")

ep = endpoints()
print("\nConfigured endpoints")
print(f"  image  : {ep['image']['provider']} / {ep['image']['model']}")
print(f"  text   : {ep['text']['provider']} / {ep['text']['model']}")
print(f"  tts    : {ep['tts']['provider']} / {ep['tts']['model']}")
print(f"  video  : {ep['video']['talking_head_endpoint']}")

print("\nChecks")
for label, ok, hint in rows:
    print(f"  {OK if ok else BAD:<18} {label}" + (f"   -> {hint}" if not ok and hint else ""))

bad = [r for r in rows if not r[1]]
print(f"\n{len(rows) - len(bad)}/{len(rows)} passed")
sys.exit(1 if bad else 0)
