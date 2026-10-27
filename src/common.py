"""Shared paths, config loading, tiny ledger."""
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
QUEUE = OUT / "queue"
STATE = ROOT / "state"
LEDGER = STATE / "ledger.json"

for d in (ASSETS / "character", OUT, QUEUE, STATE):
    d.mkdir(parents=True, exist_ok=True)


def load(name):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


def character(name=None):
    """Character config. Override with CHARACTER_CONFIG=character_v3.json."""
    name = name or env("CHARACTER_CONFIG", "character.json")
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


def character_dir():
    return ASSETS / env("CHARACTER_DIR", "character")


def endpoints():
    return load("endpoints.json")


def prompt(name):
    with open(ROOT / "prompts" / name, encoding="utf-8") as f:
        return f.read()


def env(name, default=None):
    v = os.getenv(name, default)
    return v if v not in ("", None) and not str(v).startswith("REPLACE") else default


def dry_run():
    return env("DRY_RUN", "0") == "1" or "--dry-run" in os.sys.argv


def ledger():
    if LEDGER.exists():
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"published": [], "failed": []}


def save_ledger(data):
    tmp = LEDGER.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEDGER)


def today():
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def slug(text, n=40):
    keep = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    return "-".join(keep.lower().split())[:n] or "post"


def pick_music(mood):
    mdir = Path(env("MUSIC_DIR", str(ASSETS / "music")))
    if not mdir.exists():
        return None
    files = [p for p in mdir.rglob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a")]
    if not files:
        return None
    files.sort()
    idx = abs(hash(mood)) % len(files)
    return str(files[idx])
