# Reel styles — kaunsa style, kaise, kitna kharcha

@vamiiika_official jaisa feed = **motion + outfit cuts**, talking-head nahi.
Teen legal tareeke, sab is repo me wired:

| Style | Kya hai | Cost per reel | Key chahiye | Command |
|---|---|---|---|---|
| **Montage** (default) | 6-8 face-locked shots, beat pe hard cuts, hook text, music | **₹0** | ❌ | `python scripts/montage.py --count 1` |
| **Motion transfer** | licensed dance clip + apni character image → apni ladki wahi dance karti hai | ₹15-40 (fal) | `FAL_KEY` | `python scripts/motion.py --ref assets/motion/clip.mp4 --source pexels.com` |
| **Text-to-video** | prompt se dance/action (koi reference nahi) | ₹20-60 | `FAL_KEY` | `FAL_ENDPOINT` set karke pipeline se |

## Montage (aaj live hai)
8 shots `assets/shots/` me (gym, saree, night, cafe, beach, street, dance, co-ord).
Koi AI video nahi — sirf ffmpeg. Har reel me shots rotate hote hain, hook tag se match karta hai.

## Motion transfer — sabse zaroori baat
Character swap **legal** hai jab reference clip **licensed** ho. Face/body aapki AI character ka
hota hai, motion stock dancer ka — koi real person copy nahi hota.

**Free + legal clip sources** (modification + commercial allowed):
- pexels.com/search/videos/dance/ (Pexels license)
- pixabay.com/videos/search/dance/ (Pixabay license)
- coverr.co/search?q=dance · mixkit.co/free-stock-video/dance/

**Banned:** Instagram / TikTok / YouTube se kisi ka reel download karke swap karna.
Ye deepfake + copyright hai → Fanvue/Meta permanent ban, IT Act 66E/67, DMCA.
`scripts/motion.py` me allowlist hai — wo source reject kar deta hai.

## Free manual path (bina FAL_KEY)
1. kling.ai ya higgsfield.ai kholo (daily free credits)
2. Motion control me: apni shot (`assets/shots/shot_02.png`) + licensed clip daalo
3. Output download karo → `assets/motion/my_dance.mp4`
4. `python scripts/motion.py --local assets/motion/my_dance.mp4 --hook "SHE CAN MOVE"`
   → 1080x1920 + hook + music + repo me commit (gallery me aa jayegi)

## Schedule
Roz 3 reels: 07:00 / 13:00 / 19:00 IST (`pipeline.yml` cron). Manual: Actions → Run workflow → task=`reel`.

---

## Auto-post (website + Instagram dono)

Har `build` / `reel` / `motion` task ke baad `ci_run.py` khud check karta hai ki
`IG_USER_ID` + `IG_ACCESS_TOKEN` hain ya nahi:

- **Hain** -> nayi reel turant Instagram pe post (Reels API), phir website pe.
- **Nahi hain** -> skip, reel sirf website pe (log: `auto-post: Instagram keys missing`).

Keys daalne ke baad kuch extra nahi karna — schedule khud post karega.

## Motion / swap reels (asli video, slideshow nahi)

```
assets/motion/  <- licensed clip (Mixkit/Pexels) ya aapki khud ki video
        +  assets/shots/ (character face)
        -> scripts/swap_reel.py --auto --count 2
   1080x1920 reel (hook + music) -> website -> Instagram
```
Cron: **08:00 aur 18:00 IST**. FAL_KEY na ho to script skip karti hai (build fail nahi hoti).
Free manual: kling.ai / higgsfield.ai output `assets/motion/` me daalo ->
`python scripts/swap_reel.py --local assets/motion/my_clip.mp4`.
