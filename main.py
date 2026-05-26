import sys
import os
from datetime import date
from generate_script import generate_script
from create_video import create_carousel_video
from post_youtube import post_youtube
from post_instagram import post_instagram
from post_instagram_story import post_instagram_story

SLOT_CONFIG = {
    "youtube":   {"platforms": ["youtube"],              "slot_number": 0},  # 17:30
    "instagram": {"platforms": ["instagram"],            "slot_number": 1},  # 18:30
    "both":      {"platforms": ["youtube", "instagram"], "slot_number": 2},  # 20:00
}

STORY_VIDEO = os.path.join(os.path.dirname(__file__), "videos", "stories", "story1.mp4")


def main():
    slot = sys.argv[1] if len(sys.argv) > 1 else "both"
    config      = SLOT_CONFIG.get(slot, SLOT_CONFIG["both"])
    platforms   = config["platforms"]
    slot_number = config["slot_number"]

    print(f"\n=== ZIA Content Bot — slot: {slot.upper()} | plataformas: {', '.join(platforms)} ===\n")

    print("PASO 1: Generando contenido con IA...")
    content = generate_script(slot_number)
    print(f"Tema: {content['topic']}\n")

    print("PASO 2: Renderizando carrusel...")
    video_path = create_carousel_video(content, "zia_video.mp4")

    yt_ok = ig_ok = story_ok = False

    if "youtube" in platforms:
        print("PASO 3: Publicando en YouTube...")
        try:
            post_youtube(
                video_path,
                title=content["youtube_title"],
                description=content["youtube_description"],
                tags=content["youtube_tags"],
            )
            yt_ok = True
        except Exception as e:
            print(f"YouTube error (se continúa): {e}")
    else:
        print("PASO 3: YouTube omitido para este slot.")
        yt_ok = True

    if "instagram" in platforms:
        print("PASO 4: Publicando Reel en Instagram...")
        if os.environ.get("INSTAGRAM_USERNAME"):
            try:
                post_instagram(video_path, caption=content["instagram_caption"])
                ig_ok = True
            except Exception as e:
                print(f"Instagram Reel error: {e}")

            print("PASO 5: Publicando Story en Instagram...")
            try:
                poll_index = date.today().toordinal()
                post_instagram_story(STORY_VIDEO, poll_index=poll_index)
                story_ok = True
            except Exception as e:
                print(f"Instagram Story error (no crítico): {e}")
                story_ok = True
        else:
            print("INSTAGRAM_USERNAME no configurado, saltando.")
            ig_ok = story_ok = True
    else:
        print("PASO 4: Instagram omitido para este slot.")
        ig_ok = story_ok = True

    if os.path.exists("zia_video.mp4"):
        os.remove("zia_video.mp4")

    print(f"\n{'OK' if yt_ok else 'FALLÓ'} YouTube | "
          f"{'OK' if ig_ok else 'FALLÓ'} Instagram Reel | "
          f"{'OK' if story_ok else 'FALLÓ'} Instagram Story\n")

    if not yt_ok and not ig_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
