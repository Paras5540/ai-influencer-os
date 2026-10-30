"""VModel video face/character swap — free $10 credits. Endpoint schema probe-friendly."""
import json, os, time
import requests

BASE = "https://api.vmodel.ai"

def _h():
    return {"Authorization": f"Bearer {os.environ['VMODEL_API_KEY']}",
            "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122 Safari/537.36"}

def swap(image_url, video_url, log=print):
    """Returns video URL. Raises with raw response snippet on failure."""
    payload = {"model": "video-face-swap", "input": {
        "source_image_url": image_url, "target_video_url": video_url},
        "source_image_url": image_url, "target_video_url": video_url,
        "face_image_url": image_url, "video_url": video_url}
    r = requests.post(f"{BASE}/api/tasks/v1/create", headers=_h(), json=payload, timeout=90)
    log(f"vmodel create {r.status_code}: {r.text[:300]}")
    if r.status_code >= 400:
        raise RuntimeError(f"vmodel {r.status_code}: {r.text[:200]}")
    j = r.json()
    tid = j.get("task_id") or j.get("id") or (j.get("data") or {}).get("task_id")
    for _ in range(120):
        time.sleep(5)
        s = requests.get(f"{BASE}/api/tasks/v1/{tid}", headers=_h(), timeout=60)
        d = s.json() if s.status_code < 400 else {}
        st = (d.get("status") or (d.get("data") or {}).get("status") or "").lower()
        if st in ("success", "completed", "done"):
            out = d.get("output") or d.get("data") or d
            for k in ("video_url", "url", "video"):
                v = out.get(k) if isinstance(out, dict) else None
                if isinstance(v, str) and v.startswith("http"):
                    return v
            raise RuntimeError(f"no url in: {json.dumps(d)[:250]}")
        if st in ("failed", "error"):
            raise RuntimeError(f"task failed: {json.dumps(d)[:250]}")
    raise RuntimeError("vmodel timeout")
