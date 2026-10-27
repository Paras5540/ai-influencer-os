#!/usr/bin/env python3
"""01 — Build the character ONE time.

Creates:
  assets/character/master.png      <- the identity anchor (never regenerate)
  assets/character/sheet.png       <- 6-angle sheet to sanity-check consistency
  assets/character/face.json       <- metadata + sha of master

Run once. After this, every image is an EDIT of master.png.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv  # noqa: E402

from common import ASSETS, CONFIG, ROOT, character, dry_run, endpoints, prompt  # noqa: E402
from lib import providers  # noqa: E402

load_dotenv(ROOT / ".env")

# python src/01_build_character.py --config character_v3.json --dir character_v3
CFG = "character.json"
DIR = "character"
for i, a in enumerate(sys.argv):
    if a == "--config" and i + 1 < len(sys.argv):
        CFG = sys.argv[i + 1]
    if a == "--dir" and i + 1 < len(sys.argv):
        DIR = sys.argv[i + 1]

CDIR = ASSETS / DIR
MASTER = CDIR / "master.png"
SHEET = CDIR / "sheet.png"
CDIR.mkdir(parents=True, exist_ok=True)

SHEET_PROMPT = (
    "Use the reference image as the exact identity. Produce one contact sheet: a 3x2 grid of six "
    "separate photorealistic photos of the SAME woman, plain light-grey background, thin white gutters. "
    "The face must be identical in all six: same face shape, eyebrows, eyes, nose, lips, beauty spot on "
    "the left cheekbone, same skin tone and texture. Panels: front neutral; three-quarter left; "
    "three-quarter right; full smile; full-body standing in plain t-shirt and jeans; walking mid-stride. "
    "Natural diffused daylight, phone-camera realism, visible skin texture, no retouching. "
    "No text, no labels, no numbers, no watermark."
)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def main():
    ep = endpoints()["image"]
    body = prompt("01_face_master.txt")
    m = re.search(r"## Prompt\s*\n(.+?)\n---", body, re.S)
    face_prompt = (m.group(1) if m else body).strip()

    ch = character(CFG)
    lock = ch["identity_lock"]
    extra = ""
    if lock.get("wardrobe_palette"):
        extra += f"\nWardrobe palette: {', '.join(lock['wardrobe_palette'][:3])}."
    if lock.get("signature_details"):
        extra += f"\nSignature details always present: {', '.join(lock['signature_details'][:3])}."
    if lock.get("always_on"):
        extra += f"\nAlways worn: {', '.join(lock['always_on'])}."
    face_prompt += extra

    if MASTER.exists():
        print(f"master.png already exists ({sha(MASTER)}) — refusing to overwrite.")
        print("Delete it manually if you really want a NEW character (all old content stops matching).")
        return

    if dry_run():
        print("[dry-run] would generate master face with prompt:\n")
        print(face_prompt[:800], "...\n")
        return

    print("Generating master face ...")
    blob = providers.gemini_image(face_prompt, ep["model"], aspect="3:4")
    MASTER.write_bytes(blob)
    print(f"  saved {MASTER} ({len(blob) // 1024} KB, id {sha(MASTER)})")

    print("Generating consistency sheet ...")
    try:
        sheet = providers.gemini_image(SHEET_PROMPT, ep["model"], reference_images=[str(MASTER)],
                                       aspect="3:2")
        SHEET.write_bytes(sheet)
        print(f"  saved {SHEET}")
    except Exception as e:  # noqa: BLE001
        print(f"  ! sheet failed ({e}) — master is still valid, continue")

    (CDIR / "face.json").write_text(json.dumps({
        "character_id": ch["character_id"],
        "master_sha256_16": sha(MASTER),
        "identity_lock": ch["identity_lock"],
        "face_prompt": face_prompt,
        "note": "Every future image MUST pass master.png as the reference image.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nDone. Open assets/character/master.png and check the eyes/beauty spot before proceeding.")


if __name__ == "__main__":
    main()
