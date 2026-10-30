# Recommended stack (main ne chuna — har kaam ka best option)

| Kaam | Best option | Fallback | Kharcha |
|---|---|---|---|
| Script/caption | **Gemini 2.5 Flash** | built-in template bank | ₹0 |
| Face-locked image | **Gemini 2.5 Flash Image** (nano-banana) | Pollinations (keyless) -> SeaArt LoRA | ₹0 |
| Voice | **Edge TTS** (hi-IN-SwaraNeural) | Google TTS -> ElevenLabs | ₹0 |
| **Dance / character swap** | **fal Kling 1.6 Pro Motion Control** | fal Wan 2.2 Animate (sasta) | ₹15-40/reel |
| Talking head | fal Kling Avatar | fal sync-lipsync | ₹15-30/reel |
| Music | self-generated beats | licensed clip audio | ₹0 |
| Posting | IG Graph API + YT Data API + Fanvue API | manual download | ₹0 |
| Hosting | GitHub Actions (render) + Oracle Free (dashboard) | VPS ₹350 | ₹0 |

## Reference video kahan se
- **Allowed**: `assets/motion/` me licensed clips (Mixkit / Pexels / Coverr — commercial ok),
  ya **aapki khud ki** video.
- **Not allowed**: Instagram / TikTok / YouTube se download (copyright + Meta ToS +
  Fanvue ka "no real person" rule). `scripts/motion.py` isko block karta hai.

## Automatic flow
```
08:00 / 18:00 IST  ->  swap_reel.py  ->  fal motion control  ->  1080x1920 + hook + music
                   ->  content/ (website)  ->  Instagram post (keys ho to)
```
