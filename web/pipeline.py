"""Reel pipeline for the dashboard.

Ek hi function sab kuch karta hai: script -> face-locked image -> Hindi voice -> video
-> 1080x1920 + burned captions. Jis step ki key nahi hai, us step ka free fallback chalta hai,
isliye app bina kisi key ke bhi asli reel bana deta hai (master image + Edge TTS + captions).
"""
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lib import free_stack, media, providers  # noqa: E402
import db  # noqa: E402

RENDERS = db.DATA / "renders"
RENDERS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# no-key content bank (rotates so demo mode still gives real variety)
# --------------------------------------------------------------------------- #
SCRIPTS = [
    {"hook": "Raat ko ye galti mat karna",
     "script": "Raat ko sone se pehle phone ko bedside pe rakh do, haath ke paas nahi. "
               "Mujhe teen hafte lage, par neend badal gayi. Aaj se try karo, batao kaisa laga.",
     "caption": "3 hafte ka experiment 🖤 raat ko phone door rakho\n\n#nightroutine #selfcare #mumbai #reels",
     "outfit": "black ribbed tank top", "scene": "cosy bedroom at night, warm lamp on"},
    {"hook": "200 rupaye mein best coffee",
     "script": "Bandra mein ek chhoti si jagah hai jahan cold coffee sirf do sau rupaye ki hai. "
               "Naam nahi bataungi, comment karo phir bataungi. Save kar lo, kaam aayega.",
     "caption": "Bandra ka sasta secret ☕\n\n#mumbai #cafehopping #bandra #foodie #reels",
     "outfit": "oversized white shirt", "scene": "small Bandra cafe, afternoon light"},
    {"hook": "Dating app pe red flag",
     "script": "Dating app pe ek hi red flag sabse bada hai, aur wo hai jaldi reply na karna. "
               "Jo interested hota hai, wo time nikal leta hai. Baaki sab excuse hai.",
     "caption": "sach bol diya 💀\n\n#dating #datingapps #mumbai #girltalk #reels",
     "outfit": "black oversized tee", "scene": "sitting on bed, evening lamp light"},
    {"hook": "Ek kurti, teen look",
     "script": "Ek hi kurti se teen look. Office ke liye belt aur kolhapuri, cafe ke liye jeans aur sneakers, "
               "shaadi ke liye dupatta aur jhumke. Teen look, ek hi kapda.",
     "caption": "ek kurti, teen look 👗\n\n#fashionhacks #budgetfashion #indianwear #reels",
     "outfit": "cotton kurti", "scene": "bedroom mirror, daylight"},
    {"hook": "Gym ke baad ka sach",
     "script": "Gym ke baad jo thakan hoti hai na, wahi asli progress hai. "
               "Motivation nahi, habit kaam karti hai. Roz nahi, par hafte me teen din.",
     "caption": "habit > motivation\n\n#gym #fitness #mumbai #reels",
     "outfit": "black tank top", "scene": "bedroom, morning window light"},
]


# --------------------------------------------------------------------------- #
def _setting(k, default=None):
    v = db.get_setting(k, default)
    if v not in (None, ""):
        os.environ.setdefault(k, str(v))
    return v or default


def _cfg(k, default):
    return _setting(k, default)


def _character():
    name = _setting("CHARACTER_CONFIG", "character_v5_locked.json")
    path = ROOT / "config" / name
    if not path.exists():
        path = ROOT / "config" / "character.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _master():
    d = _setting("CHARACTER_DIR", "character_v6")
    p = ROOT / "assets" / d / "master.png"
    if not p.exists():
        for cand in sorted((ROOT / "assets").glob("character*/master.png")):
            p = cand
            break
    return p


def _script_item():
    cal = ROOT / "config" / "content_calendar.csv"
    idx = int(time.time() // 86400) % 5
    base = SCRIPTS[idx]
    if cal.exists():
        try:
            import csv
            rows = list(csv.DictReader(open(cal, encoding="utf-8")))
            r = rows[int(time.time() // 86400) % len(rows)]
            base = dict(base, topic=r["topic"], pillar=r["pillar"])
        except Exception:  # noqa: BLE001
            pass
    return base


def _llm_script(ch):
    key = _setting("GEMINI_API_KEY")
    if not key:
        return None
    os.environ["GEMINI_API_KEY"] = key
    try:
        prompt = (
            "Indian AI influencer ke liye ek 10-12 second ka Hindi reel script likho. "
            "Hinglish allowed. Style: friend se baat, warm, thodi cheeky. "
            "Return strict JSON with keys: hook (max 6 words), script (25-40 Hindi words), "
            "caption (2 lines + 5 hashtags), outfit, scene, expression.")
        out = providers.gemini_text(prompt, _cfg("GEMINI_TEXT_MODEL", "gemini-2.5-flash"),
                                    json_mode=True, tries=2)
        return out
    except Exception as e:  # noqa: BLE001
        db.log(f"LLM script failed, using template: {e}", "warn", "script")
        return None


def _image(ch, item, workdir):
    master = _master()
    dest = workdir / "scene.png"
    key = _setting("GEMINI_API_KEY")
    if key:
        os.environ["GEMINI_API_KEY"] = key
        try:
            prompt = (
                "Using the reference image as the exact identity of this woman, keep her face, hair "
                "and makeup 100% unchanged. Change only the scene: "
                f"{item.get('scene', 'cosy bedroom')}. Outfit: {item.get('outfit', 'black tank top')}. "
                "Photorealistic phone photo, visible skin texture and pores, warm natural light, "
                "no beauty filter, no airbrushing, vertical 9:16, chest-up framing, space at the bottom "
                "for captions. No text, no watermark.")
            blob = providers.gemini_image(prompt, _cfg("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
                                          reference_images=[str(master)], aspect="9:16", tries=2)
            dest.write_bytes(blob)
            db.log("scene image generated (Gemini, face-locked)", "info", "image")
            return dest
        except Exception as e:  # noqa: BLE001
            db.log(f"image gen failed, using master: {str(e)[:160]}", "warn", "image")
    shutil.copy(master, dest)
    return dest


def _voice(ch, text, out):
    voice = ch.get("voice", {})
    provider = _cfg("TTS_PROVIDER", voice.get("provider", "edge"))
    if provider == "elevenlabs" and _setting("ELEVENLABS_API_KEY") and not str(voice.get("elevenlabs_voice_id", "")).startswith("REPLACE"):
        try:
            os.environ["ELEVENLABS_API_KEY"] = _setting("ELEVENLABS_API_KEY")
            providers.eleven_tts(text, voice["elevenlabs_voice_id"],
                                 os.environ["ELEVENLABS_API_KEY"], "eleven_multilingual_v2",
                                 voice.get("elevenlabs_settings", {}), str(out))
            db.log("voice: ElevenLabs", "info", "voice")
            return out
        except Exception as e:  # noqa: BLE001
            db.log(f"ElevenLabs failed, falling back to free Edge TTS: {str(e)[:120]}", "warn", "voice")
    free_stack.edge_tts(
        text, str(out),
        voice=voice.get("edge_voice", "hi-IN-SwaraNeural"),
        rate=voice.get("edge_rate", "+4%"),
        pitch=voice.get("edge_pitch", "+4Hz"))
    db.log("voice: Edge TTS (free)", "info", "voice")
    return out


def _video_size():
    """LOW_MEM=1 -> 720x1280 (free 512MB-1GB hosts). Warna 1080x1920."""
    if os.getenv("LOW_MEM", "0") == "1":
        return 720, 1280
    h = int(os.getenv("VIDEO_HEIGHT", "1920"))
    return (1080, 1920) if h >= 1920 else (720, 1280)


def _kenburns(image, dur, out):
    w, h = _video_size()
    low = os.getenv("LOW_MEM", "0") == "1"
    if low:
        # sasta motion: upscale -> crop -> slow pan (zoompan CPU-heavy hota hai)
        vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
              f"crop={w}:{h}:x='(iw-ow)/2 + 40*sin(t/5)':y='(ih-oh)/2',"
              f"fps=30")
    else:
        vf = (f"scale={w*1.5:.0f}:{h*1.5:.0f}:force_original_aspect_ratio=increase,"
              f"crop={w*1.5:.0f}:{h*1.5:.0f},"
              f"zoompan=z='min(1.02+0.0006*on,1.14)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps=30")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(image), "-t", f"{dur:.2f}",
           "-vf", vf, "-c:v", "libx264",
           "-preset", os.getenv("FFMPEG_PRESET", "veryfast" if low else "veryfast"),
           "-crf", os.getenv("FFMPEG_CRF", "24" if low else "22"),
           "-pix_fmt", "yuv420p", "-threads", "2", str(out)]
    media.run(cmd)
    return out


def _talking(image, audio, workdir, dur):
    key = _setting("FAL_KEY")
    if not key:
        return None
    os.environ["FAL_KEY"] = key
    try:
        ep = json.loads((ROOT / "config" / "endpoints.json").read_text(encoding="utf-8"))
        vcfg = ep["video"]
        img_url = providers.upload_public(str(image))
        aud_url = providers.upload_public(str(audio))
        endpoint = _cfg("FAL_ENDPOINT", vcfg["talking_head_endpoint"])
        prompt = ("Subtle natural head movement, realistic blinking, lips perfectly synced to the audio, "
                  "camera locked. Same person, same face, same clothes as the image. "
                  "Photorealistic phone video. No text.")
        if "lipsync" in endpoint or "sync" in endpoint:
            base = providers.fal_run(_cfg("FAL_BROLL_ENDPOINT", vcfg["broll_endpoint"]), {
                "image_url": img_url, "prompt": prompt, "duration": "5",
                "aspect_ratio": "9:16", "resolution": vcfg.get("resolution", "720p")})
            url = providers._find_media_url(base) if hasattr(providers, "_find_media_url") else None
            if not url:
                return None
            broll = workdir / "broll.mp4"
            providers.download(url, broll)
            out = providers.fal_run(endpoint, {
                "video_url": providers.upload_public(str(broll)), "audio_url": aud_url})
        else:
            out = providers.fal_run(endpoint, {"image_url": img_url, "audio_url": aud_url,
                                               "prompt": prompt})
        url = None
        for k in ("video", "video_url", "url", "output"):
            v = out.get(k) if isinstance(out, dict) else None
            if isinstance(v, dict):
                v = v.get("url")
            if isinstance(v, str) and v.startswith("http"):
                url = v
                break
        if not url:
            return None
        dest = workdir / "head.mp4"
        providers.download(url, dest)
        db.log("talking video generated (fal)", "info", "video")
        return dest
    except Exception as e:  # noqa: BLE001
        db.log(f"talking video failed, using ken-burns: {str(e)[:160]}", "warn", "video")
        return None


# --------------------------------------------------------------------------- #
def build_reel(job_id):
    ch = _character()
    item = _script_item()
    llm = _llm_script(ch)
    if llm:
        item = dict(item, **{k: v for k, v in llm.items() if v})
        db.log("script: LLM", "info", "script")
    else:
        db.log("script: template bank (no LLM key)", "info", "script")

    workdir = RENDERS / f"job{job_id}"
    workdir.mkdir(parents=True, exist_ok=True)

    db.update_job(job_id, progress=15, message="script ready")
    image = _image(ch, item, workdir)

    db.update_job(job_id, progress=40, message="voice")
    audio = _voice(ch, item["script"], workdir / "voice.mp3")
    dur = media.duration(str(audio))

    db.update_job(job_id, progress=60, message="video")
    raw = _talking(image, audio, workdir, dur) or _kenburns(image, dur, workdir / "kb.mp4")

    db.update_job(job_id, progress=85, message="captions + render")
    ass = media.build_ass(item["script"], item.get("hook"), dur, str(workdir / "caps.ass"))
    final = workdir / "final.mp4"
    music = None
    mdir = ROOT / "assets" / "music"
    tracks = [p for p in mdir.glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a")] if mdir.exists() else []
    if tracks:
        music = str(random.choice(tracks))
    w, h = _video_size()
    media.render_reel(str(raw), str(audio), ass, str(final), music=music, width=w, height=h,
                      preset=os.getenv("FFMPEG_PRESET", "veryfast" if os.getenv("LOW_MEM") == "1" else "medium"))

    thumb = workdir / "thumb.jpg"
    media.run(["ffmpeg", "-y", "-ss", "1", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(thumb)])

    pid = db.add_post(
        job_id=job_id, title=item.get("topic", item.get("hook", "reel")),
        hook=item.get("hook", ""), caption=item.get("caption", ""),
        video=str(final.relative_to(db.DATA)), thumb=str(thumb.relative_to(db.DATA)),
        platform="instagram", status="ready", created=time.time())
    db.update_job(job_id, status="done", progress=100,
                  message=f"reel ready (#{pid}, {dur:.1f}s)")
    db.log(f"reel #{pid} ready in {dur:.1f}s", "info", "pipeline")
    return pid


# --------------------------------------------------------------------------- #
# publishing
# --------------------------------------------------------------------------- #
def publish_instagram(post):
    tok, uid = _setting("IG_ACCESS_TOKEN"), _setting("IG_USER_ID")
    if not (tok and uid):
        raise RuntimeError("Instagram keys missing (IG_USER_ID + IG_ACCESS_TOKEN)")
    ver = "v21.0"
    path = db.DATA / post["video"]
    url = providers.upload_public(str(path))
    r = requests.post(f"https://graph.facebook.com/{ver}/{uid}/media", timeout=120, data={
        "media_type": "REELS", "video_url": url,
        "caption": post["caption"] + "\n\n#AIgeneratedcharacter", "share_to_feed": "true",
        "access_token": tok})
    if r.status_code >= 400:
        raise RuntimeError(f"IG container: {r.text[:250]}")
    cid = r.json()["id"]
    for _ in range(60):
        time.sleep(10)
        s = requests.get(f"https://graph.facebook.com/{ver}/{cid}",
                         params={"fields": "status_code", "access_token": tok}, timeout=60).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError("IG processing error")
    p = requests.post(f"https://graph.facebook.com/{ver}/{uid}/media_publish", timeout=120,
                      data={"creation_id": cid, "access_token": tok})
    if p.status_code >= 400:
        raise RuntimeError(f"IG publish: {p.text[:250]}")
    return p.json()["id"]


def publish_fanvue(post, price_cents=None):
    tok = _setting("FANVUE_ACCESS_TOKEN")
    if not tok:
        raise RuntimeError("Fanvue token missing")
    import importlib.util
    spec = importlib.util.spec_from_file_location("fanvue_cli", SRC / "06_fanvue.py")
    mod = importlib.util.module_from_spec(spec)
    os.environ["FANVUE_ACCESS_TOKEN"] = tok
    spec.loader.exec_module(mod)
    uid = mod.upload_media(str(db.DATA / post["video"]), "video")
    out = mod.create_post(post["caption"], [uid],
                          price_cents=price_cents or int(_setting("FANVUE_PRICE_CENTS", 699)),
                          audience="subscribers")
    return out.get("uuid")


def publish_youtube(post):
    cid, sec, ref = (_setting("YT_CLIENT_ID"), _setting("YT_CLIENT_SECRET"),
                     _setting("YT_REFRESH_TOKEN"))
    if not (cid and sec and ref):
        raise RuntimeError("YouTube keys missing")
    t = requests.post("https://oauth2.googleapis.com/token", timeout=60, data={
        "client_id": cid, "client_secret": sec, "refresh_token": ref,
        "grant_type": "refresh_token"}).json()["access_token"]
    path = db.DATA / post["video"]
    size = os.path.getsize(path)
    meta = {"snippet": {"title": (post["hook"] or post["title"])[:90] + " #Shorts",
                        "description": post["caption"] + "\n#AIgeneratedcharacter",
                        "categoryId": "22"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos",
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={"Authorization": f"Bearer {t}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
        json=meta, timeout=120)
    if init.status_code >= 400:
        raise RuntimeError(f"YT init: {init.text[:200]}")
    with open(path, "rb") as f:
        up = requests.put(init.headers["Location"], data=f, timeout=1800,
                          headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
    if up.status_code >= 400:
        raise RuntimeError(f"YT upload: {up.text[:200]}")
    return up.json().get("id")
