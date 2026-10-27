"""ffmpeg helpers: duration probe, ASS subtitle build (Devanagari-safe), final reel render."""
import os
import re
import subprocess


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd[:6])}...\n{p.stderr[-1500:]}")
    return p.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def _ts(sec):
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Noto Sans Devanagari,96,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,8,70,70,120,1
Style: Cap,Noto Sans Devanagari,78,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,70,70,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _strip_punct(s):
    return re.sub(r"[।,.!?\"“”]", "", s).strip()


def build_ass(text, hook_text, total_dur, out_path, words_per_cue=4, hook_sec=2.2):
    """Proportional word timing (no ASR needed, which is fine for short scripts).
    For exact word-level sync run faster-whisper and replace cues with real timestamps."""
    words = [w for w in text.replace("\n", " ").split(" ") if w.strip()]
    cues = [" ".join(words[i:i + words_per_cue]) for i in range(0, len(words), words_per_cue)]
    if not cues:
        cues = [_strip_punct(text)]

    speak_start = hook_sec if hook_text else 0.0
    span = max(total_dur - speak_start, 1.0)
    per = span / len(cues)

    lines = [ASS_HEADER]
    if hook_text:
        lines.append(
            f"Dialogue: 1,{_ts(0)},{_ts(hook_sec)},Hook,,0,0,0,,"
            f"{{\\fad(150,150)}}{hook_text.upper()}\n"
        )
    t = speak_start
    for c in cues:
        lines.append(
            f"Dialogue: 0,{_ts(t)},{_ts(t + per)},Cap,,0,0,0,,{{\\fad(90,90)}}{c}\n"
        )
        t += per
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return out_path


def render_reel(video_in, audio_in, ass_file, out_path, music=None,
                width=1080, height=1920, music_gain=0.12, src_audio=False,
                preset=None):
    """Crop/scale to 9:16, burn captions, attach voice (+optional ducked music)."""
    dur = duration(audio_in)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"ass={ass_file}"
    )
    cmd = ["ffmpeg", "-y", "-i", video_in, "-i", audio_in]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
        filter_complex = (
            f"[0:v]{vf}[v];"
            f"[1:a]volume=1.0[a1];"
            f"[2:a]volume={music_gain},afade=t=in:st=0:d=0.8[am];"
            f"[a1][am]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", vf, "-map", "0:v:0", "-map", "1:a:0"]

    cmd += [
        "-t", f"{dur:.2f}",
        "-c:v", "libx264", "-preset", preset or os.getenv("FFMPEG_PRESET", "medium"),
        "-crf", os.getenv("FFMPEG_CRF", "20"),
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", out_path,
    ]
    run(cmd)
    return out_path


def kenburns(image, dur, out_path, width=1080, height=1920, low_mem=False):
    """Free fallback motion jab video model available na ho."""
    if low_mem:
        vf = (f"scale={width*2}:{height*2}:force_original_aspect_ratio=increase,"
              f"crop={width}:{height}:x='(iw-ow)/2 + 40*sin(t/5)':y='(ih-oh)/2',fps=30")
    else:
        vf = (f"scale={int(width*1.5)}:{int(height*1.5)}:force_original_aspect_ratio=increase,"
              f"crop={int(width*1.5)}:{int(height*1.5)},"
              f"zoompan=z='min(1.02+0.0006*on,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"d=1:s={width}x{height}:fps=30")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(image), "-t", f"{dur:.2f}", "-vf", vf,
         "-c:v", "libx264", "-preset", os.getenv("FFMPEG_PRESET", "veryfast"),
         "-crf", os.getenv("FFMPEG_CRF", "23"), "-pix_fmt", "yuv420p", str(out_path)])
    return out_path
