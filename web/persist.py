"""GitHub pe data save/restore — Render free ka disk reset ho to kuch na ude."""
import base64, json, os
import requests
import db

TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = os.getenv("GITHUB_REPO", "")
BR = os.getenv("GITHUB_BRANCH", "main")
ON = bool(TOKEN and REPO)


def _h():
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


def _get(path):
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",
                     headers=_h(), params={"ref": BR}, timeout=40)
    if r.status_code != 200:
        return None, None
    j = r.json()
    return base64.b64decode(j["content"]), j.get("sha")


def save_file(local_path, repo_path, msg="data: save"):
    if not ON or not os.path.exists(local_path):
        return False
    try:
        data = open(local_path, "rb").read()
        _, sha = _get(repo_path)
        body = {"message": msg, "content": base64.b64encode(data).decode(), "branch": BR}
        if sha:
            body["sha"] = sha
        r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{repo_path}",
                         headers=_h(), json=body, timeout=180)
        return r.status_code < 300
    except Exception:
        return False


def save_settings():
    if not ON:
        return False
    try:
        state = db.all_settings()
        p = db.DATA / "_settings.json"
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return save_file(str(p), "state/dashboard_settings.json", "state: settings")
    except Exception:
        return False


def restore_settings():
    if not ON:
        return 0
    try:
        raw, _ = _get("state/dashboard_settings.json")
        if not raw:
            return 0
        data = json.loads(raw.decode())
        n = 0
        for k, v in data.items():
            if v and not db.get_setting(k):
                db.set_setting(k, v)
                os.environ[k] = v
                n += 1
        if n:
            db.log(f"settings restored from GitHub: {n}", "info", "persist")
        return n
    except Exception:
        return 0


def save_reel(post):
    if not ON:
        return False
    ok = False
    try:
        vid = str(db.DATA / post["video"])
        ok = save_file(vid, f"data/reels/{os.path.basename(os.path.dirname(vid))}.mp4", "data: reel")
        if post.get("thumb"):
            save_file(str(db.DATA / post["thumb"]),
                      f"data/thumbs/{os.path.basename(os.path.dirname(vid))}.jpg", "data: thumb")
    except Exception:
        pass
    return ok
