"""Background worker: ek thread jobs chalata hai, doosra scheduler (cron) dekhta hai."""
import json
import threading
import time
from datetime import datetime

import db
import persist
import pipeline


def _run_job(job):
    jid, kind, payload = job["id"], job["kind"], json.loads(job["payload"] or "{}")
    db.update_job(jid, status="running", progress=5, message=f"{kind} started")
    db.log(f"job #{jid} {kind} started", "info", "worker")
    try:
        if kind == "build":
            pipeline.build_reel(jid)
            persist.save_settings()
            return
        if kind == "swap":
            pipeline.swap_video(jid, payload["file"],
                                hook=payload.get("hook") or "NEW DROP",
                                caption=payload.get("caption") or "")
            persist.save_settings()
            try:
                newest = db.list_posts(1)[0]
                persist.save_reel(newest)
            except Exception:
                pass
            return
        if kind == "publish":
            platform = payload["platform"]
            post = db.get_post(payload["post_id"])
            if not post:
                raise RuntimeError("post not found")
            if platform == "instagram":
                rid = pipeline.publish_instagram(post)
            elif platform == "youtube":
                rid = pipeline.publish_youtube(post)
            elif platform == "fanvue":
                rid = pipeline.publish_fanvue(post, payload.get("price_cents"))
            else:
                raise RuntimeError(f"unknown platform {platform}")
            db.update_post(post["id"], status="published",
                           published_at=datetime.now().isoformat(timespec="seconds"),
                           remote_id=str(rid))
            db.update_job(jid, status="done", progress=100, message=f"published to {platform}")
            persist.save_reel(post)
            persist.save_settings()
            db.log(f"post #{post['id']} published to {platform}", "info", "publish")
            return
        if kind == "auto":
            task = payload["task"]
            post = db.next_ready_post("instagram")
            if not post:
                db.update_job(jid, status="skipped", progress=100, message="no reel ready")
                db.log(f"auto {task}: queue empty", "warn", "scheduler")
                return
            rid = {"ig": lambda: pipeline.publish_instagram(post),
                   "youtube": lambda: pipeline.publish_youtube(post),
                   "fanvue": lambda: pipeline.publish_fanvue(post)}[task]()
            db.update_post(post["id"], status="published",
                           published_at=datetime.now().isoformat(timespec="seconds"),
                           remote_id=str(rid))
            db.update_job(jid, status="done", progress=100, message=f"auto {task} done")
            return
        raise RuntimeError(f"unknown job kind {kind}")
    except Exception as e:  # noqa: BLE001
        db.update_job(jid, status="failed", progress=100, message=str(e)[:300])
        db.log(f"job #{jid} failed: {e}", "error", "worker")


def worker_loop():
    db.log("worker started", "info", "worker")
    while True:
        try:
            job = db.next_queued_job()
            if not job:
                time.sleep(2)
                continue
            _run_job(job)
        except Exception as e:  # noqa: BLE001
            db.log(f"worker crash (recovered): {e}", "error", "worker")
            time.sleep(3)


CATCHUP_HOURS = float(__import__("os").getenv("CATCHUP_HOURS", "6"))


def scheduler_loop():
    """Due tasks fire karta hai. Agar host so raha tha (free hosting), to jaagte hi
    pichhle CATCHUP_HOURS ke andar ka missed task bhi chala deta hai."""
    db.log("scheduler started (with catch-up)", "info", "scheduler")
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            due = []
            for row in db.list_schedule():
                if not row["enabled"] or row["last_run"] == today:
                    continue
                hh, mm = (int(x) for x in row["at"].split(":"))
                at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if now < at:
                    continue
                age_h = (now - at).total_seconds() / 3600.0
                due.append((at, age_h, row))

            due.sort(key=lambda x: x[0])
            for i, (at, age_h, row) in enumerate(due):
                last = i == len(due) - 1
                if age_h > CATCHUP_HOURS:
                    db.mark_run(row["id"], today)
                    db.log(f"missed too long, skipped: {row['task']} @ {row['at']}", "warn", "scheduler")
                    continue
                if not last:
                    # ek hi baar catch-up karo, baaki skip (spam na ho)
                    db.mark_run(row["id"], today)
                    db.log(f"catch-up collapsed: {row['task']} @ {row['at']}", "warn", "scheduler")
                    continue
                db.mark_run(row["id"], today)
                if row["task"] == "build":
                    db.create_job("build", {})
                else:
                    db.create_job("auto", {"task": row["task"]})
                db.log(f"scheduled task fired: {row['task']} @ {row['at']} "
                       f"(delay {age_h*60:.0f} min)", "info", "scheduler")
        except Exception as e:  # noqa: BLE001
            db.log(f"scheduler error: {e}", "error", "scheduler")
        time.sleep(20)


def start():
    threading.Thread(target=worker_loop, daemon=True, name="worker").start()
    threading.Thread(target=scheduler_loop, daemon=True, name="scheduler").start()
