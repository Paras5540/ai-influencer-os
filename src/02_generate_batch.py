#!/usr/bin/env python3
"""02 — Generate a batch of ready-to-post reels into out/queue/.

Per item:  script (LLM) -> scene image (edit of master face) -> Hindi voice (TTS)
           -> talking video (image+audio) -> 1080x1920 render with burned captions
           -> item.json (caption, hashtags, hook) for the publisher.

Usage:
  python src/02_generate_batch.py            # uses MAX_POSTS_PER_DAY, default 1
  python src/02_generate_batch.py --count 3
  python src/02_generate_batch.py --dry-run  # prints the plan + prompts, calls nothing
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv  # noqa: E402

from common import (ASSETS, CONFIG, OUT, QUEUE, ROOT, character, character_dir, dry_run,  # noqa: E402
                    endpoints, env, pick_music, prompt, slug, today)
from lib import media, providers, voice as voice_lib  # noqa: E402

load_dotenv(ROOT / ".env")

MASTER = character_dir() / "master.png"

SCENE_TEMPLATE = """Using the reference image as the exact identity of the woman, keep her face, facial
features, skin tone, hairline and the beauty spot on her left cheekbone 100% unchanged. Change only
the following:

- SCENE: {scene}
- OUTFIT: {outfit}
- EXPRESSION: {expression}. Keep the same slight closed-mouth smile as the reference where possible.
- CAMERA: {camera}
- LIGHT: {light}
- MOOD / GRADE: {grade}

Photorealistic, phone-camera realism, visible skin texture, natural imperfect hair strands, no beauty
retouching, no airbrushing, no plastic skin. Vertical 9:16 framing, chest-up, eyes on the upper third,
clean space in the lower third for captions. No text, no watermark, no logo."""

TALK_PROMPT = ("Subtle natural head movement, realistic blinking, tiny eyebrow reactions, lips perfectly "
               "synced to the audio, shoulders barely moving, hair strands drifting. Camera locked, no zoom, "
               "no cuts. Same person, same face, same clothes as the image. Photorealistic phone-camera video.")


# --------------------------------------------------------------------------- #
def calendar_rows():
    p = CONFIG / "content_calendar.csv"
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_script(ch, ep, row, day_index):
    sys_p = prompt("03_script_brain.md")
    sys_p = sys_p.replace("{name}", ch["name"]).replace("{persona}", ch["persona_one_liner"])
    user = (f"Aaj ka post #{day_index}. Content pillar: {row['pillar']}. "
            f"Topic hint: {row['topic']}. Filming constraint: ek hi location, ek hi shot. "
            f"Return only the JSON object described in the schema.")
    return providers.gemini_text(user, ep["text"]["model"], system=sys_p)


def make_image(item, ep):
    p = SCENE_TEMPLATE.format(
        scene=item["scene"], outfit=item["outfit"], expression=item["expression"].replace("_", " "),
        camera=item["camera"], light=item["light"], grade=item["grade"])
    blob = providers.gemini_image(p, ep["image"]["model"], reference_images=[str(MASTER)], aspect="9:16")
    return blob


def _find_media_url(obj, exts=(".mp4", ".mov", ".webm", ".mp3", ".wav")):
    if isinstance(obj, str):
        return obj if obj.startswith("http") and obj.lower().split("?")[0].endswith(exts) else None
    if isinstance(obj, dict):
        for k in ("url", "video", "video_url", "output", "audio", "audio_url"):
            if k in obj:
                found = _find_media_url(obj[k], exts)
                if found:
                    return found
        for v in obj.values():
            found = _find_media_url(v, exts)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = _find_media_url(v, exts)
            if found:
                return found
    return None


def make_video(image_path, audio_path, ep, workdir, duration_hint):
    vcfg = ep["video"]
    img_url = providers.upload_public(str(image_path))
    aud_url = providers.upload_public(str(audio_path))
    endpoint = vcfg["talking_head_endpoint"]

    if "lipsync" in endpoint or "sync" in endpoint or "latentsync" in endpoint:
        # two-step: b-roll first, then lip-sync the audio onto it
        base = providers.fal_run(vcfg["broll_endpoint"], {
            "image_url": img_url,
            "prompt": TALK_PROMPT,
            "duration": "5",
            "aspect_ratio": "9:16",
            "resolution": vcfg.get("resolution", "720p"),
        })
        broll_url = _find_media_url(base)
        if not broll_url:
            raise RuntimeError(f"no video url in b-roll response: {json.dumps(base)[:300]}")
        broll = workdir / "broll.mp4"
        providers.download(broll_url, broll)
        broll_public = providers.upload_public(str(broll))
        out = providers.fal_run(endpoint, {"video_url": broll_public, "audio_url": aud_url})
    else:
        # single-step avatar model (image + audio -> talking video)
        out = providers.fal_run(endpoint, {
            "image_url": img_url,
            "audio_url": aud_url,
            "prompt": TALK_PROMPT,
        })

    url = _find_media_url(out)
    if not url:
        raise RuntimeError(f"no video url in response: {json.dumps(out)[:500]}")
    dest = workdir / "raw_head.mp4"
    providers.download(url, dest)
    return dest


# --------------------------------------------------------------------------- #
STUB = {
    "topic": "topik", "pillar": "city_life",
    "hook": "Ek minute ruk jao",
    "script": "Ek minute ruk jao. Ye jo maine pehna hai na, iska total sirf teen sau rupaye hai. "
              "Aur haan, ye teen mahine se chal raha hai. Save kar lo, batao kaisa laga.",
    "expression": "warm_smile", "outfit": "oversized cream shirt", "scene": "Bandra cafe",
    "camera": "chest-up phone selfie", "light": "warm window light from left",
    "grade": "warm filmic", "broll_motion": "micro head nods, blink",
    "on_screen_hook": "TEEN SAU RUPAYE", "caption_instagram": "stub caption",
    "caption_youtube": "stub", "music_mood": "lofi",
}


def build_one(row, idx, ep):
    ch = character()
    if dry_run():
        item = dict(STUB, topic=row["topic"], pillar=row["pillar"])
    else:
        try:
            item = make_script(ch, ep, row, idx)
        except Exception as e:  # noqa: BLE001
            print(f"  ! script failed ({str(e)[:80]}) — template use kar rahe hain")
            item = dict(STUB, topic=row["topic"], pillar=row["pillar"], hook=row["topic"][:40],
                        caption_instagram=f"{row['topic']}\n\n#reels #mumbai #AIgeneratedcharacter")
    name = f"{today()}-{idx:02d}-{slug(item['topic'], 26)}-{datetime.now().strftime('%H%M%S')}"
    workdir = OUT / name
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"  script: {item['hook']}")

    if dry_run():
        json.dump(item, open(workdir / "item.json", "w"), ensure_ascii=False, indent=2)
        print(f"  [dry-run] plan written to {workdir / 'item.json'}")
        return workdir

    # 1. scene image — always an edit of the master face
    if not MASTER.exists():
        raise RuntimeError("assets/character/master.png missing — run src/01_build_character.py first")
    img = workdir / "scene.png"
    try:
        img.write_bytes(make_image(item, ep))
        print(f"  image : {img} (AI scene)")
    except Exception as e:  # noqa: BLE001
        print(f"  ! image gen failed ({str(e)[:80]}) — master face use kar rahe hain")
        import shutil as _sh
        _sh.copy(MASTER, img)

    # 2. voice (free Edge TTS by default — see config/endpoints.json tts.provider)
    audio = workdir / "voice.mp3"
    voice_lib.speak(item["script"], ch, ep, audio)
    dur = media.duration(audio)
    print(f"  voice : {dur:.1f}s")

    # 3. talking video (fail ho to free ken-burns motion)
    try:
        raw = make_video(img, audio, ep, workdir, dur)
        print(f"  video : {raw} (talking head)")
    except Exception as e:  # noqa: BLE001
        print(f"  ! video gen failed ({str(e)[:80]}) — ken-burns fallback")
        low = env("LOW_MEM", "0") == "1"
        w, h = (720, 1280) if low else (1080, 1920)
        raw = media.kenburns(img, dur, workdir / "kb.mp4", w, h, low)

    # 4. render 9:16 with burned captions + optional music
    ass = media.build_ass(item["script"], item.get("on_screen_hook"), dur, str(workdir / "caps.ass"))
    final = workdir / "final.mp4"
    media.render_reel(str(raw), str(audio), ass, str(final), music=pick_music(item.get("music_mood", "")))
    print(f"  final : {final} ({media.duration(str(final)):.1f}s)")

    meta = {
        "id": name,
        "created": datetime.now().astimezone().isoformat(),
        "video": str(final),
        "caption_instagram": item["caption_instagram"],
        "caption_youtube": item.get("caption_youtube", item["hook"]),
        "hook": item["hook"],
        "pillar": item["pillar"],
        "topic": item["topic"],
        "ai_disclosure": ch["posting"]["ai_label_text"],
        "status": "queued",
    }
    json.dump(meta, open(workdir / "item.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return workdir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=int(env("MAX_POSTS_PER_DAY", "1")))
    ap.add_argument("--dry-run", action="store_true", help="print the plan, call no paid API")
    args = ap.parse_args()
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"

    ep = endpoints()
    rows = calendar_rows()
    start = datetime.now().timetuple().tm_yday
    print(f"Building {args.count} item(s){' [DRY RUN]' if dry_run() else ''}")

    for i in range(args.count):
        row = rows[(start + i) % len(rows)]
        print(f"\n[{i + 1}/{args.count}] pillar={row['pillar']} topic={row['topic']}")
        try:
            build_one(row, start + i, ep)
        except Exception as e:  # noqa: BLE001
            print(f"  ! failed: {e}")
            if i + 1 >= args.count:
                raise
    print("\nDone. Publish with: python src/05_publish.py")


if __name__ == "__main__":
    main()
