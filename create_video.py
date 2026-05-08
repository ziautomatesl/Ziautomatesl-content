"""
Video creation pipeline (Remotion-only):
  1. Copy audio → remotion/public/audio.mp3
  2. Write props.json  { topic, wordTimings, durationInSeconds, audioSrc }
  3. npx remotion render → zia_video.mp4  (audio baked in via <Audio> component)
"""

import os
import json
import shutil
import subprocess
import time
from moviepy import AudioFileClip

_HERE        = os.path.dirname(os.path.abspath(__file__))
REMOTION_DIR = os.path.join(_HERE, "remotion")
PUBLIC_DIR   = os.path.join(REMOTION_DIR, "public")


def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # 1. Get audio duration
    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()

    # 2. Copy audio to public/ so Remotion can access it
    audio_dest = os.path.join(PUBLIC_DIR, "audio.mp3")
    shutil.copy2(audio_path, audio_dest)

    # 3. Write props
    props = {
        "topic":             topic,
        "wordTimings":       word_timings,
        "durationInSeconds": duration,
        "audioSrc":          "audio.mp3",
        "seed":              int(time.time()) % 100,  # different theme order each video
    }
    props_path = os.path.join(REMOTION_DIR, "props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    # 4. Remotion render → final MP4 (audio included via <Audio> component)
    abs_output = os.path.abspath(output_path)
    print("Renderizando vídeo con Remotion...")
    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts", "ZiaVideo",
            "--props",         "props.json",
            "--output",        abs_output,
            "--codec",         "h264",
            "--image-format",  "jpeg",
            "--jpeg-quality",  "85",
            "--concurrency",   "4",
            "--log",           "verbose",
        ],
        cwd=REMOTION_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )

    # Cleanup temp files
    for p in [audio_dest, props_path]:
        try:
            os.remove(p)
        except Exception:
            pass

    return output_path
