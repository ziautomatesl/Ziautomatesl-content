"""
Video creation pipeline:
  1. moviepy  → bg_video.mp4 (Pexels clips, hard cuts every 3s, fast)
  2. Remotion → overlay.webm (transparent VP8: subtitles, UI, flash)
  3. ffmpeg   → zia_video.mp4 (composite bg + overlay + audio)
"""

import os
import json
import shutil
import subprocess
from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips, ColorClip
from get_backgrounds import fetch_background_videos

_HERE        = os.path.dirname(os.path.abspath(__file__))
REMOTION_DIR = os.path.join(_HERE, "remotion")
PUBLIC_DIR   = os.path.join(REMOTION_DIR, "public")

W, H           = 1080, 1920
SCENE_SECONDS  = 3.0   # hard cut interval (must match ZiaVideo.tsx)
RENDER_FPS     = 24    # must match Root.tsx


# ── Step 1: background video (moviepy) ────────────────────────────────────────

def _make_bg_video(video_paths, duration, output_path):
    """Concatenate Pexels clips in 3-second hard-cut scenes to fill duration."""
    def _fit(p):
        c = VideoFileClip(p).without_audio()
        if c.w / c.h > W / H:
            c = c.resized(height=H)
        else:
            c = c.resized(width=W)
        x1 = max(0, (c.w - W) // 2)
        y1 = max(0, (c.h - H) // 2)
        return c.cropped(x1=x1, y1=y1, width=W, height=H)

    clips = []
    for p in video_paths:
        try:
            clips.append(_fit(p))
        except Exception as e:
            print(f"  Skipping {p}: {e}")

    if not clips:
        bg = ColorClip((W, H), color=(0, 8, 20), duration=duration)
        bg.write_videofile(output_path, fps=RENDER_FPS, codec="libx264",
                           preset="faster", logger=None)
        return

    # Build SCENE_SECONDS-long segments cycling through clips
    scenes, t, seg_idx = [], 0.0, 0
    while t < duration:
        seg_dur = min(SCENE_SECONDS, duration - t)
        clip    = clips[seg_idx % len(clips)]
        # Stagger start within clip to avoid identical repeats
        offset = (seg_idx // len(clips)) * 2.0 % max(clip.duration - seg_dur, 0.01)
        end    = min(offset + seg_dur, clip.duration)
        seg    = clip.subclipped(offset, end)
        if seg.duration < seg_dur - 0.05:      # clip shorter than segment → loop
            seg = seg.loop(duration=seg_dur)   # type: ignore[attr-defined]
        else:
            seg = seg.with_duration(seg_dur)
        scenes.append(seg)
        t       += seg_dur
        seg_idx += 1

    bg = concatenate_videoclips(scenes)
    bg.write_videofile(output_path, fps=RENDER_FPS, codec="libx264",
                       preset="faster", logger=None)


# ── Step 2: Remotion overlay (transparent WebM VP8) ───────────────────────────

def _render_overlay(props, output_path):
    """Run Remotion to render the transparent UI overlay."""
    props_path = os.path.join(REMOTION_DIR, "props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    abs_output = os.path.abspath(output_path)
    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts", "ZiaVideo",
            "--props",        "props.json",
            "--output",       abs_output,
            "--codec",        "vp8",
            "--image-format", "png",
            "--pixel-format", "yuva420p",
            "--concurrency",  "4",
            "--log",          "verbose",
        ],
        cwd=REMOTION_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )


# ── Step 3: ffmpeg composite ───────────────────────────────────────────────────

def _composite(bg_path, overlay_path, audio_path, output_path):
    """Composite bg + transparent overlay + audio into final MP4."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", bg_path,
            "-i", overlay_path,
            "-i", audio_path,
            "-filter_complex",
            "[1:v]format=rgba[ov];[0:v][ov]overlay=0:0[v]",
            "-map", "[v]",
            "-map", "2:a",
            "-c:v", "libx264", "-preset", "faster", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ],
        check=True,
    )


# ── Public entry point ─────────────────────────────────────────────────────────

def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()

    # 1. Background video
    print(f"Descargando vídeos Pexels para '{topic}'...")
    raw_paths = fetch_background_videos(topic, n=3)

    print("Preparando vídeo de fondo...")
    bg_path = os.path.join(_HERE, "bg_video.mp4")
    _make_bg_video(raw_paths, duration, bg_path)

    for p in raw_paths:
        try: os.remove(p)
        except Exception: pass

    # 2. Remotion overlay
    props = {
        "topic":           topic,
        "wordTimings":     word_timings,
        "durationInSeconds": duration,
    }
    overlay_path = os.path.join(_HERE, "overlay.webm")
    print("Renderizando overlay con Remotion...")
    _render_overlay(props, overlay_path)

    # 3. ffmpeg composite
    print("Compositando vídeo final con ffmpeg...")
    _composite(bg_path, overlay_path, audio_path, output_path)

    # Cleanup temp files
    for p in [bg_path, overlay_path]:
        try: os.remove(p)
        except Exception: pass

    return output_path
