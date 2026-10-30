"""FastAPI dashboard for the AI influencer system.

Run:  uvicorn web.app:app --host 0.0.0.0 --port 8000
Env:  ADMIN_PASSWORD (default: changeme), APP_SECRET (cookie token)
"""
import hashlib
import json
import os
import secrets
import shutil
import sys
import time
from pathlib import Path

# Schedule hamesha IST me chale, host ka timezone kuch bhi ho
os.environ.setdefault("TZ", "Asia/Kolkata")
try:
    time.tzset()
except Exception:  # noqa: BLE001
    pass

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent
for p in (str(WEB), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import db  # noqa: E402
import integrations  # noqa: E402
import persist  # noqa: E402
import pipeline  # noqa: E402
import worker  # noqa: E402

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
TOKEN = os.getenv("APP_SECRET") or hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()[:32]
db.init()

app = FastAPI(title="AI Influencer OS", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(WEB / "static")), name="static")
app.mount("/media", StaticFiles(directory=str(db.DATA)), name="media")


# --------------------------------------------------------------------------- #
def authed(req: Request) -> bool:
    return req.cookies.get("sid") == TOKEN


def guard(req: Request):
    if not authed(req):
        raise HTTPException(status_code=401, detail="login required")


@app.on_event("startup")
def _startup():
    persist.restore_settings()
    worker.start()
    db.log("dashboard started", "info", "app")


# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/system")
def system(req: Request):
    guard(req)
    from datetime import datetime
    import shutil
    total = sum(f.stat().st_size for f in db.DATA.rglob("*") if f.is_file())
    s = db.all_settings()
    return {"timezone": os.environ.get("TZ", "UTC"),
            "now": datetime.now().isoformat(timespec="seconds"),
            "builds_per_day": sum(1 for r in db.list_schedule() if r["task"] == "build" and r["enabled"]),
            "ffmpeg": shutil.which("ffmpeg") or "",
            "data_mb": round(total / 1048576, 1),
            "low_mem": s.get("LOW_MEM", "0"),
            "tts": s.get("TTS_PROVIDER", "edge"),
            "image_model": s.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
            "character": s.get("CHARACTER_CONFIG", "character_v5_locked.json")}


@app.get("/")
def index():
    return FileResponse(str(WEB / "static" / "index.html"))


@app.get("/api/me")
def me(req: Request):
    return {"authed": authed(req)}


@app.post("/api/login")
def login(payload: dict):
    if (payload.get("password") or "") != ADMIN_PASSWORD:
        db.log("failed login attempt", "warn", "auth")
        raise HTTPException(status_code=401, detail="wrong password")
    resp = JSONResponse({"ok": True})
    resp.set_cookie("sid", TOKEN, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp


@app.post("/api/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("sid")
    return resp


# --------------------------------------------------------------------------- #
@app.get("/api/stats")
def stats(req: Request):
    guard(req)
    return db.stats()


@app.get("/api/jobs")
def jobs(req: Request):
    guard(req)
    return db.list_jobs()


@app.get("/api/logs")
def logs(req: Request, after: int = 0, limit: int = 200):
    guard(req)
    return db.list_logs(limit=limit, after_id=after)


# --------------------------------------------------------------------------- #
@app.get("/api/integrations")
def get_integrations(req: Request):
    guard(req)
    cur = db.all_settings()
    groups = []
    for g in integrations.schema():
        fields = []
        for f in g["fields"]:
            v = cur.get(f["key"]) or ""
            default = f.get("default", "")
            fields.append({
                "key": f["key"], "label": f["label"], "hint": f.get("hint", ""),
                "url": f.get("url", ""), "secret": bool(f.get("secret")),
                "required": bool(f.get("required")), "choices": f.get("choices"),
                "default": default,
                "set": bool(v),
                "value": v if not f.get("secret") else "",
                "masked": (v[:4] + "..." + v[-3:]) if (v and f.get("secret") and len(v) > 8) else (v if v else ""),
            })
        groups.append({"id": g["id"], "title": g["title"], "subtitle": g.get("subtitle", ""),
                       "fields": fields})
    return {"groups": groups, "count": len(integrations.KEYS)}


@app.post("/api/integrations")
def save_integrations(req: Request, payload: dict):
    guard(req)
    changed, skipped = [], []
    for k, v in (payload or {}).items():
        if k not in integrations.KEYS:
            skipped.append(k)
            continue
        if v is None or str(v).strip() == "":
            continue
        db.set_setting(k, str(v).strip())
        os.environ[k] = str(v).strip()
        changed.append(k)
    db.log(f"integrations updated: {', '.join(changed) or 'none'}", "info", "settings")
    return {"ok": True, "changed": changed, "skipped": skipped}


@app.post("/api/integrations/test")
def test_integrations(req: Request):
    guard(req)
    res = integrations.run_tests(db.all_settings())
    db.log(f"connection test: {sum(1 for r in res if r['ok'])}/{len(res)} ok", "info", "settings")
    return res


@app.get("/api/export-env")
def export_env(req: Request):
    guard(req)
    from fastapi.responses import PlainTextResponse
    body = integrations.env_file(db.all_settings())
    db.log("env exported from dashboard", "info", "settings")
    return PlainTextResponse(body, media_type="text/plain",
                             headers={"Content-Disposition": 'attachment; filename=".env"'})


# --------------------------------------------------------------------------- #
@app.get("/api/character")
def get_character(req: Request):
    guard(req)
    cfg_name = db.get_setting("CHARACTER_CONFIG", "character_v5_locked.json")
    cfg_path = ROOT / "config" / cfg_name
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    master = pipeline._master()
    rel = master.relative_to(db.DATA) if str(master).startswith(str(db.DATA)) else None
    url = None
    if rel:
        url = f"/media/{rel.as_posix()}"
    else:
        # copy once into data so the browser can load it
        dest = db.DATA / "character_master.png"
        if not dest.exists():
            shutil.copy(master, dest)
        url = "/media/character_master.png"
    return {"name": cfg.get("name", "Character"), "id": cfg.get("character_id"),
            "master_url": url, "master_path": str(master.relative_to(ROOT)),
            "identity": cfg.get("identity_lock", {}), "styling": cfg.get("styling_defaults", {}),
            "config_file": cfg_name}


@app.post("/api/character/upload")
async def upload_character(req: Request, file: UploadFile = File(...)):
    guard(req)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="image file chahiye (png/jpg)")
    d = ROOT / "assets" / db.get_setting("CHARACTER_DIR", "character_v6")
    d.mkdir(parents=True, exist_ok=True)
    if (d / "master.png").exists():
        shutil.copy(d / "master.png", d / f"master_backup_{secrets.token_hex(3)}.png")
    data = await file.read()
    (d / "master.png").write_bytes(data)
    (db.DATA / "character_master.png").write_bytes(data)
    db.log(f"character master replaced ({len(data)//1024} KB)", "info", "character")
    return {"ok": True, "bytes": len(data)}


# --------------------------------------------------------------------------- #
@app.post("/api/build")
def build(req: Request, payload: dict | None = None):
    guard(req)
    count = int((payload or {}).get("count", 1))
    ids = [db.create_job("build", {}) for _ in range(max(1, min(count, 5)))]
    db.log(f"{len(ids)} build job(s) queued", "info", "app")
    return {"jobs": ids}


@app.get("/api/posts")
def posts(req: Request):
    guard(req)
    return db.list_posts()


@app.post("/api/posts/{pid}")
def edit_post(req: Request, pid: int, payload: dict):
    guard(req)
    if "caption" in payload:
        db.update_post(pid, caption=payload["caption"])
    return {"ok": True}


@app.post("/api/publish")
def publish(req: Request, payload: dict):
    guard(req)
    jid = db.create_job("publish", {"post_id": payload["post_id"],
                                    "platform": payload.get("platform", "instagram"),
                                    "price_cents": payload.get("price_cents")})
    db.log(f"publish job queued for post #{payload['post_id']}", "info", "app")
    return {"job": jid}


# --------------------------------------------------------------------------- #
@app.post("/api/upload_video")
async def upload_video(req: Request, file: UploadFile = File(...), hook: str = Form("")):
    """Website se video upload -> character swap job."""
    guard(req)
    if not (file.filename or "").lower().endswith((".mp4", ".mov", ".m4v")):
        raise HTTPException(status_code=400, detail="mp4/mov video chahiye")
    updir = db.DATA / "uploads"
    updir.mkdir(parents=True, exist_ok=True)
    dest = updir / f"{secrets.token_hex(4)}_{file.filename}"
    dest.write_bytes(await file.read())
    jid = db.create_job("swap", {"file": str(dest), "hook": hook})
    db.log(f"upload received: {file.filename} ({dest.stat().st_size//1024} KB) -> job #{jid}",
           "info", "upload")
    return {"job": jid, "file": dest.name}


@app.get("/api/uploads")
def list_uploads(req: Request):
    guard(req)
    updir = db.DATA / "uploads"
    if not updir.exists():
        return []
    return [{"name": p.name, "kb": p.stat().st_size // 1024}
            for p in sorted(updir.glob("*.mp4")) + sorted(updir.glob("*.mov"))]


# --------------------------------------------------------------------------- #
@app.get("/api/schedule")
def schedule(req: Request):
    guard(req)
    return db.list_schedule()


@app.post("/api/schedule")
def set_schedule(req: Request, payload: dict):
    guard(req)
    for row in payload.get("rows", []):
        db.set_schedule(int(row["id"]), at=row.get("at"), enabled=row.get("enabled"))
    return {"ok": True}
