"""SQLite storage for the dashboard: settings, jobs, posts, schedule, logs."""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DATA = Path(os.getenv("APP_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT, status TEXT, progress INTEGER DEFAULT 0, message TEXT,
  payload TEXT, created REAL, updated REAL
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER, title TEXT, hook TEXT, caption TEXT, video TEXT, thumb TEXT,
  platform TEXT, status TEXT, price_cents INTEGER, scheduled_at TEXT,
  published_at TEXT, remote_id TEXT, created REAL
);
CREATE TABLE IF NOT EXISTS schedule (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task TEXT, at TEXT, enabled INTEGER DEFAULT 1, last_run TEXT
);
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, level TEXT, source TEXT, message TEXT
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        # sensible defaults: 3 builds a day, publish slots
        if not c.execute("SELECT COUNT(*) n FROM schedule").fetchone()["n"]:
            for task, at in [("build", "07:00"), ("build", "13:00"), ("build", "19:00"),
                             ("fanvue", "09:00"), ("ig", "12:30"),
                             ("ig", "20:30"), ("fanvue", "22:00")]:
                c.execute("INSERT INTO schedule(task, at, enabled) VALUES (?,?,1)", (task, at))


# --------------------------------------------------------------------------- #
# settings
# --------------------------------------------------------------------------- #
def get_setting(key, default=None):
    with conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if r is None:
        return os.getenv(key, default)
    return r["value"]


def set_setting(key, value):
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def all_settings():
    with conn() as c:
        rows = c.execute("SELECT key, value FROM settings").fetchall()
    out = {r["key"]: r["value"] for r in rows}
    for k in ("GEMINI_API_KEY", "FAL_KEY", "ELEVENLABS_API_KEY", "IG_ACCESS_TOKEN",
              "FANVUE_ACCESS_TOKEN", "YT_REFRESH_TOKEN"):
        if k not in out and os.getenv(k):
            out[k] = os.getenv(k)
    return out


# --------------------------------------------------------------------------- #
# jobs
# --------------------------------------------------------------------------- #
def create_job(kind, payload=None):
    now = time.time()
    with conn() as c:
        cur = c.execute(
            "INSERT INTO jobs(kind,status,progress,message,payload,created,updated) "
            "VALUES(?,?,?,?,?,?,?)",
            (kind, "queued", 0, "queued", json.dumps(payload or {}), now, now))
        return cur.lastrowid


def update_job(job_id, **kw):
    if not kw:
        return
    kw["updated"] = time.time()
    sets = ", ".join(f"{k}=?" for k in kw)
    with conn() as c:
        c.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*kw.values(), job_id))


def next_queued_job():
    with conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
    return dict(r) if r else None


def get_job(job_id):
    with conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(r) if r else None


def list_jobs(limit=30):
    with conn() as c:
        rows = c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# posts
# --------------------------------------------------------------------------- #
def add_post(**kw):
    kw.setdefault("created", time.time())
    cols = ", ".join(kw)
    qs = ", ".join("?" for _ in kw)
    with conn() as c:
        cur = c.execute(f"INSERT INTO posts({cols}) VALUES({qs})", tuple(kw.values()))
        return cur.lastrowid


def list_posts(limit=60):
    with conn() as c:
        rows = c.execute("SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_post(pid):
    with conn() as c:
        r = c.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
    return dict(r) if r else None


def update_post(pid, **kw):
    sets = ", ".join(f"{k}=?" for k in kw)
    with conn() as c:
        c.execute(f"UPDATE posts SET {sets} WHERE id=?", (*kw.values(), pid))


def next_ready_post(platform):
    with conn() as c:
        r = c.execute("SELECT * FROM posts WHERE status='ready' AND platform=? ORDER BY id LIMIT 1",
                      (platform,)).fetchone()
    return dict(r) if r else None


# --------------------------------------------------------------------------- #
# schedule
# --------------------------------------------------------------------------- #
def list_schedule():
    with conn() as c:
        rows = c.execute("SELECT * FROM schedule ORDER BY at").fetchall()
    return [dict(r) for r in rows]


def set_schedule(sid, at=None, enabled=None):
    kw = {}
    if at is not None:
        kw["at"] = at
    if enabled is not None:
        kw["enabled"] = 1 if enabled else 0
    if not kw:
        return
    sets = ", ".join(f"{k}=?" for k in kw)
    with conn() as c:
        c.execute(f"UPDATE schedule SET {sets} WHERE id=?", (*kw.values(), sid))


def mark_run(sid, day):
    with conn() as c:
        c.execute("UPDATE schedule SET last_run=? WHERE id=?", (day, sid))


# --------------------------------------------------------------------------- #
# logs
# --------------------------------------------------------------------------- #
def log(message, level="info", source="app"):
    with conn() as c:
        c.execute("INSERT INTO logs(ts,level,source,message) VALUES(?,?,?,?)",
                  (time.time(), level, source, str(message)[:2000]))
    try:
        print(f"[{source}/{level}] {message}", flush=True)
    except Exception:  # noqa: BLE001
        pass


def list_logs(limit=200, after_id=0):
    with conn() as c:
        rows = c.execute("SELECT * FROM logs WHERE id>? ORDER BY id DESC LIMIT ?",
                         (after_id, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]


def stats():
    with conn() as c:
        q = lambda s: c.execute(s).fetchone()[0]  # noqa: E731
        return {
            "reels_ready": q("SELECT COUNT(*) FROM posts WHERE status='ready'"),
            "published": q("SELECT COUNT(*) FROM posts WHERE status='published'"),
            "jobs_running": q("SELECT COUNT(*) FROM jobs WHERE status='running'"),
            "jobs_failed": q("SELECT COUNT(*) FROM jobs WHERE status='failed'"),
        }
