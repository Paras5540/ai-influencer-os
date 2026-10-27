"""All integrations/API settings in one schema — website isi se form banati hai.

Har field: key, label, hint, where-to-get URL, secret?, required?, default.
Naya provider add karna ho to sirf yahan ek entry likho, UI apne aap bana degi.
"""

GROUPS = [
    {
        "id": "ai",
        "title": "Content AI",
        "subtitle": "Script + face-locked images (free tier se kaam ho jata hai)",
        "fields": [
            {"key": "GEMINI_API_KEY", "label": "Gemini API key", "secret": True, "required": True,
             "hint": "Script aur face-locked scenes. Free tier, card nahi.",
             "url": "https://aistudio.google.com/apikey", "test": "gemini"},
            {"key": "GEMINI_TEXT_MODEL", "label": "Text model", "default": "gemini-2.5-flash",
             "hint": "Script/caption brain"},
            {"key": "GEMINI_IMAGE_MODEL", "label": "Image model", "default": "gemini-2.5-flash-image",
             "hint": "Face-locked image edits (nano-banana)"},
        ],
    },
    {
        "id": "voice",
        "title": "Voice",
        "subtitle": "Edge TTS free hai — kuch add karne ki zaroorat nahi",
        "fields": [
            {"key": "TTS_PROVIDER", "label": "TTS provider", "default": "edge",
             "hint": "edge = free unlimited · elevenlabs = paid, better emotion", "choices": ["edge", "elevenlabs"]},
            {"key": "ELEVENLABS_API_KEY", "label": "ElevenLabs API key (optional)", "secret": True,
             "hint": "Sirf tab chahiye jab provider=elevenlabs", "url": "https://elevenlabs.io/app/settings/api-keys",
             "test": "elevenlabs"},
            {"key": "ELEVENLABS_VOICE_ID", "label": "ElevenLabs voice ID", "hint": "Hindi female voice ka ID"},
        ],
    },
    {
        "id": "video",
        "title": "Video (optional)",
        "subtitle": "Na ho to ken-burns motion chalta hai — reels phir bhi banti hain",
        "fields": [
            {"key": "FAL_KEY", "label": "fal.ai API key", "secret": True,
             "hint": "Talking-head video. Free 5/day browser me, API paid (~₹15-25/reel).",
             "url": "https://fal.ai/dashboard/keys", "test": "fal"},
            {"key": "FAL_ENDPOINT", "label": "Talking-head endpoint",
             "default": "fal-ai/kling-video/v1.6/standard/avatar",
             "hint": "fal.ai/models pe current ID dekh lo"},
            {"key": "FAL_BROLL_ENDPOINT", "label": "B-roll / motion endpoint",
             "default": "fal-ai/kling-video/v2/master/image-to-video"},
            {"key": "LOW_MEM", "label": "Low memory mode", "default": "0",
             "hint": "1 = 720x1280 + ultrafast (free 512MB-1GB server ke liye)", "choices": ["0", "1"]},
        ],
    },
    {
        "id": "publish",
        "title": "Publishing — Instagram + YouTube",
        "subtitle": "Public tier (SFW reels). Keys na ho to download karke manually post karo",
        "fields": [
            {"key": "IG_USER_ID", "label": "Instagram user ID", "hint": "Graph API explorer se milta hai",
             "url": "https://developers.facebook.com/tools/explorer/", "test": "instagram"},
            {"key": "IG_ACCESS_TOKEN", "label": "Instagram access token", "secret": True,
             "hint": "60 din me expire hota hai", "test": "instagram"},
            {"key": "IG_APP_ID", "label": "App ID (optional)", "hint": "Token refresh ke liye"},
            {"key": "IG_APP_SECRET", "label": "App secret (optional)", "secret": True},
            {"key": "YT_CLIENT_ID", "label": "YouTube client ID", "url": "https://console.cloud.google.com/apis/credentials"},
            {"key": "YT_CLIENT_SECRET", "label": "YouTube client secret", "secret": True},
            {"key": "YT_REFRESH_TOKEN", "label": "YouTube refresh token", "secret": True,
             "hint": "OAuth playground se", "test": "youtube"},
        ],
    },
    {
        "id": "premium",
        "title": "Premium tier — Fanvue",
        "subtitle": "Paid adult tier. AI accounts allowed (80/20 split)",
        "fields": [
            {"key": "FANVUE_ACCESS_TOKEN", "label": "Fanvue access token", "secret": True,
             "hint": "api.fanvue.com OAuth se. --check se verify hota hai",
             "url": "https://api.fanvue.com/docs", "test": "fanvue"},
            {"key": "FANVUE_REFRESH_TOKEN", "label": "Fanvue refresh token", "secret": True,
             "hint": "Token expire hone par auto-refresh"},
            {"key": "FANVUE_CLIENT_ID", "label": "Fanvue client ID", "hint": "Aapke Fanvue app ka"},
            {"key": "FANVUE_CLIENT_SECRET", "label": "Fanvue client secret", "secret": True},
            {"key": "FANVUE_PRICE_CENTS", "label": "PPV price (cents)", "default": "699",
             "hint": "699 = $6.99 · minimum 300"},
        ],
    },
    {
        "id": "ops",
        "title": "Automation",
        "subtitle": "Schedule, character aur catch-up",
        "fields": [
            {"key": "CHARACTER_CONFIG", "label": "Character config", "default": "character_v5_locked.json"},
            {"key": "CHARACTER_DIR", "label": "Character folder", "default": "character_v6"},
            {"key": "MAX_POSTS_PER_DAY", "label": "Max posts per day", "default": "2"},
            {"key": "CATCHUP_HOURS", "label": "Catch-up window (hours)", "default": "6",
             "hint": "Host sota tha to jaagte hi itne ghante ka missed task chalta hai"},
            {"key": "MUSIC_DIR", "label": "Music folder", "default": "assets/music"},
        ],
    },
]

# optional extra LLM gateway (OpenAI-compatible: Groq / OpenRouter / 100M-token provider)
EXTRA = {
    "id": "gateway",
    "title": "Custom LLM gateway (optional)",
    "subtitle": "Kisi bhi OpenAI-compatible provider ko script brain banao",
    "fields": [
        {"key": "OPENAI_BASE_URL", "label": "Base URL", "hint": "e.g. https://api.groq.com/openai/v1"},
        {"key": "OPENAI_API_KEY", "label": "API key", "secret": True},
        {"key": "OPENAI_MODEL", "label": "Model", "hint": "e.g. llama-3.3-70b-versatile"},
    ],
}

ALL_GROUPS = GROUPS + [EXTRA]
KEYS = {f["key"] for g in ALL_GROUPS for f in g["fields"]}


def schema():
    return ALL_GROUPS


# --------------------------------------------------------------------------- #
def run_tests(settings):
    """Har configured service ko ping karta hai. Network error = fail, not crash."""
    import requests
    out = []

    def add(name, ok, detail=""):
        out.append({"name": name, "ok": bool(ok), "detail": str(detail)[:160]})

    # ffmpeg + free voice (local, no key)
    import shutil
    add("ffmpeg", bool(shutil.which("ffmpeg")),
        shutil.which("ffmpeg") or "install: apt install ffmpeg")
    try:
        import edge_tts  # noqa: F401
        add("Edge TTS (free voice)", True, "installed, unlimited")
    except Exception as e:  # noqa: BLE001
        add("Edge TTS (free voice)", False, f"pip install edge-tts ({str(e)[:60]})")

    g = settings.get("GEMINI_API_KEY")
    if g:
        try:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                             headers={"x-goog-api-key": g}, timeout=25)
            ok = r.status_code == 200
            add("Gemini", ok, f"HTTP {r.status_code}" + ("" if ok else " — key check karo"))
        except Exception as e:  # noqa: BLE001
            add("Gemini", False, str(e)[:100])
    else:
        add("Gemini", False, "key nahi — template mode chalega")

    e = settings.get("ELEVENLABS_API_KEY")
    if e:
        try:
            r = requests.get("https://api.elevenlabs.io/v1/user",
                             headers={"xi-api-key": e}, timeout=25)
            add("ElevenLabs", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as ex:  # noqa: BLE001
            add("ElevenLabs", False, str(ex)[:100])

    f = settings.get("FAL_KEY")
    if f:
        try:
            r = requests.get("https://rest.alpha.fal.ai/tokens/",
                             headers={"Authorization": f"Key {f}"}, timeout=25)
            add("fal.ai", r.status_code < 400, f"HTTP {r.status_code}")
        except Exception as ex:  # noqa: BLE001
            add("fal.ai", False, str(ex)[:100])

    ig_t = settings.get("IG_ACCESS_TOKEN")
    ig_u = settings.get("IG_USER_ID")
    if ig_t and ig_u:
        try:
            r = requests.get(f"https://graph.facebook.com/v21.0/{ig_u}",
                             params={"fields": "username", "access_token": ig_t}, timeout=25)
            add("Instagram", r.status_code == 200,
                r.json().get("username", f"HTTP {r.status_code}"))
        except Exception as ex:  # noqa: BLE001
            add("Instagram", False, str(ex)[:100])
    elif ig_t or ig_u:
        add("Instagram", False, "user id + token dono chahiye")

    fv = settings.get("FANVUE_ACCESS_TOKEN")
    if fv:
        try:
            r = requests.get("https://api.fanvue.com/users/me", timeout=25,
                             headers={"Authorization": f"Bearer {fv}",
                                      "X-Fanvue-API-Version": "2025-06-26"})
            add("Fanvue", r.status_code < 400,
                f"HTTP {r.status_code}" + (" (token expire? refresh karo)" if r.status_code >= 400 else ""))
        except Exception as ex:  # noqa: BLE001
            add("Fanvue", False, str(ex)[:100])

    yt = settings.get("YT_REFRESH_TOKEN")
    if yt:
        try:
            r = requests.post("https://oauth2.googleapis.com/token", timeout=25, data={
                "client_id": settings.get("YT_CLIENT_ID"),
                "client_secret": settings.get("YT_CLIENT_SECRET"),
                "refresh_token": yt, "grant_type": "refresh_token"})
            add("YouTube", r.status_code == 200,
                "token ok" if r.status_code == 200 else f"HTTP {r.status_code}")
        except Exception as ex:  # noqa: BLE001
            add("YouTube", False, str(ex)[:100])
    return out


ENV_ORDER = [
    "GEMINI_API_KEY", "GEMINI_TEXT_MODEL", "GEMINI_IMAGE_MODEL",
    "TTS_PROVIDER", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID",
    "FAL_KEY", "FAL_ENDPOINT", "FAL_BROLL_ENDPOINT", "LOW_MEM",
    "IG_USER_ID", "IG_ACCESS_TOKEN", "IG_APP_ID", "IG_APP_SECRET",
    "YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN",
    "FANVUE_ACCESS_TOKEN", "FANVUE_REFRESH_TOKEN", "FANVUE_CLIENT_ID",
    "FANVUE_CLIENT_SECRET", "FANVUE_PRICE_CENTS",
    "CHARACTER_CONFIG", "CHARACTER_DIR", "MAX_POSTS_PER_DAY", "CATCHUP_HOURS", "MUSIC_DIR",
    "OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL",
]


def env_file(settings):
    lines = ["# AI Influencer OS — generated from dashboard", "TZ=Asia/Kolkata", ""]
    for k in ENV_ORDER:
        v = settings.get(k)
        if v:
            lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"
