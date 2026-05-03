import sys
import os
from generate_script import generate_script
from create_audio import create_audio
from create_video import create_animated_video, upload_for_instagram
from post_youtube import post_youtube

def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else "morning"
    print(f"\n=== ZIA Video Bot - {slot.upper()} ===\n")

    print("PASO 1: Generando guion con IA...")
    content = generate_script()
    print(f"Tema: {content['topic']}")
    print(f"Guion:\n{content['script']}\n")

    print("PASO 2: Creando audio con voz IA...")
    audio_path, word_timings = create_audio(content["script"], "zia_audio.mp3")
    print(f"Palabras detectadas: {len(word_timings)}")

    print("PASO 3: Creando video animado...")
    video_path = create_animated_video(audio_path, word_timings, "zia_video.mp4")

    print("PASO 4: Publicando en YouTube...")
    title = content["topic"]
    description = f"{content['script']}\n\n{content['hashtags']}\n\nziautomate.netlify.app"
    post_youtube(video_path, title, description)

    for f in ["zia_audio.mp3", "zia_video.mp4"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n✅ Video publicado en YouTube!\n")

if __name__ == "__main__":
    main()
