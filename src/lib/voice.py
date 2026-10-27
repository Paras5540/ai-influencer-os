"""Voice dispatcher — free Edge TTS by default, ElevenLabs if you have it."""
import os

from . import free_stack, providers


def speak(text, ch, ep, out_path):
    cfg = ep.get("tts", {})
    provider = cfg.get("provider", "edge")
    voice = ch.get("voice", {})

    if provider == "edge":
        return free_stack.edge_tts(
            text, out_path,
            voice=voice.get("edge_voice", "hi-IN-SwaraNeural"),
            rate=voice.get("edge_rate", "+8%"),
            pitch=voice.get("edge_pitch", "+15Hz"),
        )

    vid = os.getenv("ELEVENLABS_VOICE_ID", voice.get("elevenlabs_voice_id", ""))
    if str(vid).startswith("REPLACE") or not vid:
        raise RuntimeError(
            "ElevenLabs selected in config/endpoints.json but no voice id. "
            "Set voice.elevenlabs_voice_id, or switch tts.provider to 'edge' (free).")
    return providers.eleven_tts(
        text, vid, os.getenv("ELEVENLABS_API_KEY"), cfg.get("model", "eleven_multilingual_v2"),
        voice.get("elevenlabs_settings", {}), out_path)
