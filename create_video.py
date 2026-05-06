import os
import json
import shutil
import subprocess
from moviepy import AudioFileClip
from get_backgrounds import fetch_background_videos

_HERE       = os.path.dirname(os.path.abspath(__file__))
REMOTION_DIR = os.path.join(_HERE, "remotion")
PUBLIC_DIR   = os.path.join(REMOTION_DIR, "public")


def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # Audio duration
    clip = AudioFileClip(audio_path)
    duration = clip.duration
    clip.close()

    # Copy audio to Remotion public/
    shutil.copy2(audio_path, os.path.join(PUBLIC_DIR, "audio.mp3"))

    # Download Pexels background videos into Remotion public/
    print(f"Descargando vídeos Pexels para '{topic}'...")
    raw_paths = fetch_background_videos(topic, n=3)
    bg_names = []
    for i, vp in enumerate(raw_paths):
        name = f"bg{i}.mp4"
        shutil.copy2(vp, os.path.join(PUBLIC_DIR, name))
        bg_names.append(name)
        try:
            os.remove(vp)
        except Exception:
            pass

    # Write props JSON for Remotion
    props = {
        "topic": topic,
        "audioSrc": "audio.mp3",
        "wordTimings": word_timings,
        "bgVideos": bg_names,
        "durationInSeconds": duration,
    }
    props_path = os.path.join(REMOTION_DIR, "props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    # Render video with Remotion
    abs_output = os.path.abspath(output_path)
    print("Renderizando video con Remotion...")
    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts",
            "ZiaVideo",
            "--props", "props.json",
            "--output", abs_output,
            "--log", "verbose",
        ],
        cwd=REMOTION_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )

    return output_path
