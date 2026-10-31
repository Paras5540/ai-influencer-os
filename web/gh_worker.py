"""Swap ka heavy kaam GitHub Actions me (7GB RAM) chalao — Render 512MB pe OOM nahi hoga."""
import base64, os, requests
import db, persist

REPO = os.getenv("GITHUB_REPO", "")
TOKEN = os.getenv("GITHUB_TOKEN", "")


def enabled():
    return bool(REPO and TOKEN)


def _put(path, data, msg):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    cur = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=h,
                       params={"ref": "main"}, timeout=40)
    body = {"message": msg, "content": base64.b64encode(data).decode(), "branch": "main"}
    if cur.status_code == 200:
        body["sha"] = cur.json().get("sha")
    r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=h,
                     json=body, timeout=300)
    return r.status_code < 300


def dispatch_swap(video_path, hook=""):
    if not enabled() or not os.path.exists(video_path):
        return False
    name = os.path.basename(video_path)
    data = open(video_path, "rb").read()
    if len(data) > 20 * 1024 * 1024:
        db.log("video 20MB se badi — GitHub upload skip", "warn", "gh")
        return False
    if not _put(f"assets/uploads/{name}", data, f"upload: {name}"):
        return False
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    requests.put(f"https://api.github.com/repos/{REPO}/contents/.swap_hook",
                 headers=h, json={"message": "hook", "content": base64.b64encode((hook or "NEW DROP").encode()).decode(), "branch": "main"}, timeout=60)
    r = requests.post(f"https://api.github.com/repos/{REPO}/actions/workflows/upload.yml/dispatches",
                      headers=h, json={"ref": "main"}, timeout=60)
    db.log(f"GitHub Actions dispatch: {r.status_code}", "info", "gh")
    return r.status_code < 300
