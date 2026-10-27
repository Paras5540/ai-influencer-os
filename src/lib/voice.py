"""Voice with fallback chain — koi ek fail ho to agla try hota hai.

Order (default): ElevenLabs (agar key) -> Edge TTS (free) -> Google TTS (free, cloud-safe)

Kyun chain: GitHub Actions / cloud IPs pe Microsoft Edge TTS 403 deta hai (datacenter block),
isliye cloud me Google TTS fallback zaroori hai. Local/VPS pe Edge chalta hai (best quality).

Env:
  TTS_PROVIDER=edge|elevenlabs|google   (preferred, default edge)
  TTS_ORDER=edge,google                 (explicit chain override)
  TTS_SKIP_EDGE=1                       (cloud me seedha google)
"""
import os
import shutil
import subprocess
import urllib.parse
import urllib.request

from . import free_stack, media, providers

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"}


def _edge(text, ch, out):
    v = ch.get("voice", {})
    return free_stack.edge_tts(
        text, out,
        voice=v.get("edge_voice", "hi-IN-SwaraNeural"),
        rate=v.get("edge_rate", "+4%"),
        pitch=v.get("edge_pitch", "+4Hz"),
    )


def _eleven(text, ch, ep, out):
    v = ch.get("voice", {})
    vid = os.getenv("ELEVENLABS_VOICE_ID") or v.get("elevenlabs_voice_id", "")
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key or not vid or str(vid).startswith("REPLACE"):
        raise RuntimeError("elevenlabs not configured")
    return providers.eleven_tts(text, vid, key, ep.get("tts", {}).get("model", "eleven_multilingual_v2"),
                                v.get("elevenlabs_settings", {}), out)


def _chunks(text, size=170):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def _google(text, out, lang="hi"):
    """Unofficial Google Translate TTS — free, cloud IPs pe chalta hai."""
    tmpdir = os.path.dirname(os.path.abspath(out)) or "."
    parts = []
    for i, ch in enumerate(_chunks(text)):
        url = ("https://translate.google.com/translate_tts?ie=UTF-8&q="
               + urllib.parse.quote(ch) + f"&tl={lang}&client=tw-ob&ttsspeed=1")
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=45).read()
        if len(data) < 1000:
            raise RuntimeError("google tts returned empty audio")
        p = os.path.join(tmpdir, f"_gtts_{i}.mp3")
        with open(p, "wb") as f:
            f.write(data)
        parts.append(p)

    if len(parts) == 1:
        shutil.move(parts[0], out)
    else:
        lst = os.path.join(tmpdir, "_gtts_list.txt")
        with open(lst, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        media.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                   "-c:a", "libmp3lame", "-b:a", "128k", out])
        for p in parts + [lst]:
            try:
                os.remove(p)
            except OSError:
                pass

    if not os.path.exists(out) or os.path.getsize(out) < 2000:
        raise RuntimeError("google tts produced no audio")
    return out


def _order(ep, ch):
    explicit = os.getenv("TTS_ORDER")
    if explicit:
        return [x.strip() for x in explicit.split(",") if x.strip()]
    if os.getenv("TTS_SKIP_EDGE") == "1":
        return ["elevenlabs", "google"]
    pref = os.getenv("TTS_PROVIDER") or ep.get("tts", {}).get("provider") or \
        ch.get("voice", {}).get("provider", "edge")
    chain = ["elevenlabs", "edge", "google"] if pref == "elevenlabs" else ["edge", "elevenlabs", "google"]
    return chain


def speak(text, ch, ep, out_path):
    errors = []
    for p in _order(ep, ch):
        try:
            if p == "elevenlabs":
                _eleven(text, ch, ep, out_path)
            elif p == "edge":
                _edge(text, ch, out_path)
            elif p == "google":
                _google(text, out_path, lang=ch.get("voice", {}).get("lang", "hi"))
            else:
                continue
            if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
                print(f"  voice: {p}")
                return out_path
            raise RuntimeError("empty audio")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{p}: {str(e)[:90]}")
            print(f"  ! tts {p} failed: {str(e)[:90]}")
    raise RuntimeError("all TTS providers failed -> " + " | ".join(errors))
