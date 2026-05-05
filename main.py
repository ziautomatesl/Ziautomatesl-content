import sys
import os
from generate_script import generate_script
from create_audio import create_audio
from create_video import create_animated_video
from post_youtube import post_youtube
from post_instagram import post_instagram

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
    video_path = create_animated_video(audio_path, word_timings, "zia_video.mp4",
                                       topic=content["topic"],
                                       script_text=content["script"])

    caption = f"{content['topic']}\n\n{content['script']}\n\n{content['hashtags']}\n\nziautomate.netlify.app"

    print("PASO 4: Publicando en YouTube...")
    title = content["topic"]
    description = f"{content['script']}\n\n{content['hashtags']}\n\nziautomate.netlify.app"
    post_youtube(video_path, title, description)

    print("PASO 5: Publicando en Instagram...")
    if os.environ.get("INSTAGRAM_USERNAME"):
        post_instagram(video_path, caption)
    else:
        print("INSTAGRAM_USERNAME no configurado, saltando.")

    for f in ["zia_audio.mp3", "zia_video.mp4"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n✅ Video publicado!\n")

if __name__ == "__main__":
    main()
