# Aap video upload karo -> swap -> gallery -> aapke confirm pe post

## 3 step (bas)

1. **Video daalo** — GitHub pe `assets/uploads/` folder kholo -> *Add file* -> *Upload files* ->
   apni `.mp4` drag karo -> Commit.
2. **2-4 minute wait** — `upload-swap` workflow khud chalega:
   - aapki video ka **motion** liya
   - usme **aapki ladki ka chehra** daala (character swap)
   - 1080x1920 reel + hook text + music bana ke **gallery** me daal diya
   - gallery: https://paras5540.github.io/ai-influencer-os/
3. **Confirm karke post** — Reel pehle gallery me dekho. Pasand aaye to
   Actions -> **pipeline** -> Run workflow -> task = `instagram` -> Run.
   Bas tab post hoga. (Automatic daily post chahiye to schedule already on hai.)

## Kya chahiye
- `FAL_KEY` (fal.ai) — swap engine. Bina iske workflow sirf message dega, video rakhi rahegi.
- Instagram keys (`IG_USER_ID`, `IG_ACCESS_TOKEN`) — post ke liye.

## Video rules
- Format: `.mp4`, vertical best (9:16), 10 second se lambi ho to pehle 10s liye jayenge
- Aapki video honi chahiye ya licensed — kisi aur ki Instagram reel nahi
- Ek baar me kitni bhi videos daal sakte ho, sab process hongi
- Process hone ke baad video `assets/uploads/done/` me chali jaati hai

## Free manual (bina FAL key)
kling.ai ya higgsfield.ai -> Motion Control -> apni video + `assets/shots/shot_02.png` ->
output download -> `assets/motion/` me daalo -> `python scripts/swap_reel.py --local assets/motion/my.mp4`
