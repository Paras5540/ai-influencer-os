"""Free-tier adapters. Every expensive step has a zero-cost path here.

Priority order the pipeline uses (set in config/endpoints.json):
  image : gemini (free tier) -> pollinations (keyless, unlimited-ish) -> manual (SeaArt/Lovart)
  voice : edge   (free, unlimited)  -> elevenlabs (paid, better emotion)
  video : fal 5 free/day (Wan 3) -> kling free daily credits -> captions-only reel (zero cost)

Free = slower queues + rate caps. Paid = speed. Nothing here needs a card.
"""
import asyncio
import os
import random
import time
import urllib.parse

import requests

UA = {"User-Agent": "ai-influencer-os/2.0"}


# --------------------------------------------------------------------------- #
# FREE VOICE — Microsoft Edge neural TTS (hi-IN-SwaraNeural = female Hindi)
# Unlimited, no key, no signup. This is the single best free upgrade.
# --------------------------------------------------------------------------- #
def edge_tts(text, out_path, voice="hi-IN-SwaraNeural", rate="+8%", pitch="+15Hz"):
    import edge_tts  # pip install edge-tts

    async def go():
        c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await c.save(out_path)

    asyncio.run(go())
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 2000:
        raise RuntimeError("edge-tts produced no audio")
    return out_path


# --------------------------------------------------------------------------- #
# FREE IMAGE — Pollinations (keyless text-to-image). Good for b-roll/teaser stills.
# For FACE consistency it uses the kontext model with a reference image URL.
# --------------------------------------------------------------------------- #
def pollinations_image(prompt, out_path, width=832, height=1248, model="flux",
                       seed=None, reference_url=None, timeout=240):
    seed = seed if seed is not None else random.randint(1, 10**9)
    q = urllib.parse.quote(prompt, safe="")
    url = (f"https://image.pollinations.ai/prompt/{q}"
           f"?width={width}&height={height}&model={model}&seed={seed}&nologo=true&enhance=true")
    if reference_url:
        url += f"&image={urllib.parse.quote(reference_url, safe='')}"
    for attempt in range(4):
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 20000:
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"pollinations failed: {r.status_code} {r.text[:160]}")


# --------------------------------------------------------------------------- #
# FREE VIDEO — what's actually free right now (checked Oct 2026)
# --------------------------------------------------------------------------- #
FREE_VIDEO_NOTES = {
    "fal_wan3": "fal.ai sandbox: 5 free Wan 3 generations / 24h (card on file required)",
    "kling": "Kling AI: ~3-5 free credits/day, watermark on free exports",
    "hailuo": "Hailuo / MiniMax: daily credit reset",
    "higgsfield": "Higgsfield: daily free credits, motion control (trend replication)",
    "google_flow": "Google Flow: 180 free credits/mo (1000/mo on Jio SIM promo), Veo 3.1 Fast",
    "wan_video": "wan.video: daily check-in credits, Character Swap (image + reference video)",
    "kie_kling_motion": "kie.ai: 80 free credits = 1 Kling Motion Control job",
    "visionstory": "VisionStory: 10 free credits + weekly bonus, talking photo",
}
