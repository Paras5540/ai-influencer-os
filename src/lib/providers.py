"""Thin, dependency-light API clients. Everything is config-driven so endpoint
IDs can be swapped without touching the pipeline."""
import base64
import json
import os
import time

import requests

TIMEOUT = 180


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _require(name):
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var {name}. Copy .env.example to .env and fill it.")
    return v


def retry(fn, tries=4, base=3, label=""):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            wait = base * (2 ** i)
            print(f"  ! {label or 'call'} failed ({i + 1}/{tries}): {e} — retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"{label} failed after {tries} tries: {last}")


# --------------------------------------------------------------------------- #
# Gemini — text (script brain) and image edit (nano-banana)
# --------------------------------------------------------------------------- #
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models"


def gemini_text(prompt, model, system=None, json_mode=True, temperature=0.9, tries=4):
    key = _require("GEMINI_API_KEY")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048,
            **({"responseMimeType": "application/json"} if json_mode else {}),
        },
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    def call():
        r = requests.post(f"{GEMINI}/{model}:generateContent?key={key}", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    txt = retry(call, tries=tries, label="gemini_text")
    if not json_mode:
        return txt
    txt = txt.strip()
    if txt.startswith("```"):
        txt = txt.split("```")[1]
        txt = txt[4:] if txt.lower().startswith("json") else txt
    return json.loads(txt.strip())


def gemini_image(prompt, model, reference_images=(), aspect="9:16", tries=4):
    """Image generation / edit. reference_images = local paths; the first one is the
    identity reference. Gemini returns inline base64 png."""
    key = _require("GEMINI_API_KEY")
    parts = [{"text": prompt}]
    for p in reference_images:
        with open(p, "rb") as f:
            parts.append({
                "inline_data": {
                    "mime_type": "image/png" if p.lower().endswith(".png") else "image/jpeg",
                    "data": base64.b64encode(f.read()).decode(),
                }
            })
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect},
        },
    }

    def call():
        r = requests.post(f"{GEMINI}/{model}:generateContent?key={key}", json=body, timeout=TIMEOUT)
        if r.status_code == 400 and "imageConfig" in r.text:
            body["generationConfig"].pop("imageConfig", None)   # older model builds
            r = requests.post(f"{GEMINI}/{model}:generateContent?key={key}", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for part in data["candidates"][0]["content"]["parts"]:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
        raise RuntimeError(f"No image in Gemini response: {json.dumps(data)[:400]}")

    return retry(call, tries=tries, label="gemini_image")


# --------------------------------------------------------------------------- #
# ElevenLabs TTS
# --------------------------------------------------------------------------- #
def eleven_tts(text, voice_id, api_key, model, settings, out_path):
    def call():
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"text": text, "model_id": model, "voice_settings": settings},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.content

    blob = retry(call, label="eleven_tts")
    with open(out_path, "wb") as f:
        f.write(blob)
    return out_path


# --------------------------------------------------------------------------- #
# Public temp hosting (so async video APIs can fetch our audio)
# --------------------------------------------------------------------------- #
def upload_public(path):
    """Returns a public https URL. Catbox first (stable, no key), tmpfiles fallback."""
    def catbox():
        with open(path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=TIMEOUT,
                headers={"User-Agent": "ai-influencer-os/1.0"},
            )
        r.raise_for_status()
        url = r.text.strip()
        if not url.startswith("http"):
            raise RuntimeError(f"catbox: {url[:200]}")
        return url

    try:
        return retry(catbox, tries=2, base=2, label="catbox")
    except Exception:
        pass

    def tmpfiles():
        with open(path, "rb") as f:
            r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=TIMEOUT)
        r.raise_for_status()
        u = r.json()["data"]["url"]
        return u.replace("tmpfiles.org/", "tmpfiles.org/dl/")

    return retry(tmpfiles, tries=2, base=2, label="tmpfiles")


# --------------------------------------------------------------------------- #
# fal.ai queue API (video + lipsync)
# --------------------------------------------------------------------------- #
def fal_run(endpoint, payload, poll_sec=6, timeout_sec=900):
    key = _require("FAL_KEY")
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}

    def submit():
        r = requests.post(f"https://queue.fal.run/{endpoint}", json=payload,
                          headers=headers, timeout=TIMEOUT)
        if r.status_code >= 400:
            raise RuntimeError(f"fal submit {endpoint}: {r.status_code} {r.text[:400]}")
        return r.json()

    job = retry(submit, tries=3, base=5, label=f"fal submit {endpoint}")
    status_url = job.get("status_url")
    response_url = job.get("response_url")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        time.sleep(poll_sec)
        st = requests.get(status_url, headers=headers, timeout=60).json()
        s = st.get("status")
        print(f"    fal {endpoint.split('/')[-2]} -> {s}")
        if s == "COMPLETED":
            return requests.get(response_url, headers=headers, timeout=TIMEOUT).json()
        if s in ("FAILED", "ERROR"):
            raise RuntimeError(f"fal job failed: {json.dumps(st)[:400]}")
    raise RuntimeError(f"fal job timeout after {timeout_sec}s")


def download(url, out_path):
    def call():
        r = requests.get(url, timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
        if os.path.getsize(out_path) < 1024:
            raise RuntimeError("downloaded file too small")
        return out_path

    return retry(call, tries=3, base=4, label="download")
