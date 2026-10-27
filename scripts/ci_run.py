#!/usr/bin/env python3
"""GitHub Actions runner — server ke bina.

  python scripts/ci_run.py --task build          # 1 reel banao
  python scripts/ci_run.py --task ig             # queue se 1 post IG pe
  python scripts/ci_run.py --task youtube
  python scripts/ci_run.py --task fanvue --price 699

Ledger state/ci_ledger.json me rehta hai (repo me commit hota hai) taaki duplicate na ho.
Content content/ me copy hota hai — GitHub Pages usse dikhata hai.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state" / "ci_ledger.json"
CONTENT = ROOT / "content"
OUT = ROOT / "out"


def ledger():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"days": {}, "published": []}


def save(l):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(l, ensure_ascii=False, indent=2))


def run(cmd):
    print("$", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=str(ROOT))
    if p.returncode != 0:
        raise SystemExit(f"command failed ({p.returncode})")


def build(count=1, force=False):
    l = ledger()
    today = datetime.now().strftime("%Y-%m-%d")
    done = l["days"].get(today, {}).get("built", 0)
    target = int(os.getenv("BUILDS_PER_DAY", "3"))
    if done >= target and not force:
        print(f"already built {done}/{target} today — skip")
        return
    n = count if force else min(target - done, count)
    sys.path.insert(0, str(ROOT / "scripts"))
    import montage
    montage.build(n)
    l["days"].setdefault(today, {})["built"] = done + n
    save(l)
    collect()


def collect():
    """Naye reels + meta ko content/ me daalo (Pages preview ke liye)."""
    CONTENT.mkdir(parents=True, exist_ok=True)
    index_path = CONTENT / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    known = {i["id"] for i in index}
    for meta_path in sorted(OUT.rglob("item.json")):
        try:
            m = json.loads(meta_path.read_text())
        except Exception:  # noqa: BLE001
            continue
        pid = meta_path.parent.name
        if pid in known:
            continue
        vid = Path(m.get("video", ""))
        if not vid.exists():
            continue
        dest_dir = CONTENT / pid
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(vid, dest_dir / "final.mp4")
        shutil.copy(meta_path, dest_dir / "item.json")
        poster = ""
        thumb = meta_path.parent / "thumb.jpg"
        dest_thumb = dest_dir / "thumb.jpg"
        if not thumb.exists():
            # CI me poster khud bana lo (pehle frame se)
            try:
                subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(vid), "-frames:v", "1",
                                "-q:v", "3", str(dest_thumb)],
                               check=True, capture_output=True)
                thumb = dest_thumb
            except Exception as e:  # noqa: BLE001
                print(f"poster failed for {pid}: {e}")
        if thumb.exists() and thumb != dest_thumb:
            shutil.copy(thumb, dest_thumb)
        if dest_thumb.exists():
            poster = f"{pid}/thumb.jpg"
        index.append({"id": pid, "hook": m.get("hook", ""), "caption": m.get("caption_instagram", ""),
                      "status": m.get("status", "queued"), "created": m.get("created", ""),
                      "video": f"{pid}/final.mp4", "poster": poster})
    for it in index:
        cand = CONTENT / it["id"] / "thumb.jpg"
        if not cand.exists():
            vid = CONTENT / it["id"] / "final.mp4"
            if vid.exists():
                subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(vid), "-frames:v", "1",
                                "-q:v", "3", str(cand)], capture_output=True)
        it["poster"] = f"{it['id']}/thumb.jpg" if cand.exists() else ""
    index = sorted(index, key=lambda x: x.get("created", ""), reverse=True)[:12]  # latest 40
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    # purane folders hatao (repo size control)
    keep = {i["id"] for i in index}
    for d in CONTENT.iterdir():
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d, ignore_errors=True)
    print(f"content/: {len(index)} reels")


def publish(platform, price=None):
    if platform == "fanvue":
        cmd = [sys.executable, "src/06_fanvue.py", "--queue"]
        if price:
            cmd += ["--price", str(price)]
    else:
        cmd = [sys.executable, "src/05_publish.py", "--platform",
               "ig" if platform == "instagram" else "yt", "--limit", "1"]
    run(cmd)
    l = ledger()
    l["published"].append({"at": datetime.now().isoformat(timespec="seconds"),
                           "platform": platform})
    l["published"] = l["published"][-200:]
    save(l)
    collect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True,
                    choices=["build", "reel", "instagram", "ig", "youtube", "fanvue", "collect"])
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--price", type=int, default=None)
    a = ap.parse_args()
    os.environ.setdefault("CHARACTER_CONFIG", "character_v5_locked.json")
    os.environ.setdefault("CHARACTER_DIR", "character_v6")
    if a.task in ("build", "reel"):
        build(a.count, force=(a.task == "reel"))
    elif a.task == "collect":
        collect()
    else:
        publish(a.task, a.price)


if __name__ == "__main__":
    main()
