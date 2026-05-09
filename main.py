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

    print("PASO 1: Generando guion...")
    content = generate_script(slot)
    print(f"Tema: {content['topic']}")
    print(f"Guion:\n{content['script']}\n")

    print("PASO 2: Creando audio con voz IA...")
    audio_path, word_timings = create_audio(content["script"], "zia_audio.mp3")
    print(f"Palabras detectadas: {len(word_timings)}")

    print("PASO 3: Creando video animado...")
    video_path = create_animated_video(
        audio_path, word_timings, "zia_video.mp4",
        topic=content["topic"],
        script_text=content["script"],
        highlights=content.get("highlights", []),
    )

    yt_ok = ig_ok = False

    print("PASO 4: Publicando en YouTube...")
    try:
        post_youtube(
            video_path,
            title=content["youtube_title"],
            description=content["youtube_description"],
            tags=content["youtube_tags"],
        )
        yt_ok = True
    except Exception as e:
        print(f"YouTube error (se continua): {e}")

    print("PASO 5: Publicando en Instagram...")
    if os.environ.get("INSTAGRAM_USERNAME"):
        try:
            post_instagram(video_path, caption=content["instagram_caption"])
            ig_ok = True
        except Exception as e:
            print(f"Instagram error: {e}")
    else:
        print("INSTAGRAM_USERNAME no configurado, saltando.")

    for f in ["zia_audio.mp3", "zia_video.mp4"]:
        if os.path.exists(f):
            os.remove(f)

    print(f"\n✅ YouTube: {'OK' if yt_ok else 'FALLÓ'} | Instagram: {'OK' if ig_ok else 'FALLÓ'}\n")
    if not yt_ok and not ig_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
