import os
import json
import base64
import random
from pathlib import Path

MUSIC_QUERIES = ["phonk", "trap motivation", "dark trap", "motivacional", "hustle", "viral"]


def get_track_with_uri(cl):
    """Busca un track trending de Instagram con URI descargable para el reel."""
    random.shuffle(MUSIC_QUERIES)
    for query in MUSIC_QUERIES:
        try:
            tracks = cl.search_music(query)
            # Necesitamos uri para poder mezclar el audio con el vídeo
            valid = [t for t in tracks if t.uri]
            if valid:
                track = random.choice(valid[:6])
                print(f"Música reel: '{track.title}' – {track.display_artist}")
                return track
        except Exception as e:
            print(f"Error buscando música ({query}): {e}")
    return None


def post_instagram(video_path: str, caption: str) -> str:
    from instagrapi import Client

    username    = os.environ["INSTAGRAM_USERNAME"]
    password    = os.environ["INSTAGRAM_PASSWORD"]
    session_b64 = os.environ.get("INSTAGRAM_SESSION", "")

    cl = Client()
    cl.delay_range = [2, 5]

    if session_b64:
        try:
            session = json.loads(base64.b64decode(session_b64).decode())
            cl.set_settings(session)
        except Exception as e:
            print(f"Sesión inválida, login fresco: {e}")

    cl.login(username, password)

    track = get_track_with_uri(cl)

    print("Subiendo Reel a Instagram...")
    try:
        if track:
            media = cl.clip_upload_as_reel_with_music(
                path=Path(video_path),
                caption=caption,
                track=track,
            )
        else:
            raise ValueError("No se encontró track válido")
    except Exception as e:
        print(f"Upload con música falló ({e}), subiendo sin música...")
        media = cl.clip_upload(Path(video_path), caption=caption)

    print(f"Reel publicado! ID: {media.pk}")
    return media.pk
