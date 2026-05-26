import os
import json
import base64
import random
from pathlib import Path

MUSIC_QUERIES = ["phonk", "trap motivation", "dark trap", "motivacional", "hustle", "viral"]


def get_track(cl):
    random.shuffle(MUSIC_QUERIES)
    for query in MUSIC_QUERIES:
        try:
            tracks = cl.search_music(query)
            if tracks:
                track = random.choice(tracks[:8])
                print(f"Música: '{track.title}' – {track.display_artist}")
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

    track = get_track(cl)

    print("Subiendo Reel a Instagram...")
    try:
        if track:
            # Igual que la app: pasa el track ID a Instagram, ellos ponen la música
            extra_data = cl.clip_music_extra_data(
                track=track,
                original_volume=0.0,  # vídeo sin audio original
                music_volume=1.0,     # música de Instagram al 100%
            )
            media = cl.clip_upload(Path(video_path), caption=caption, extra_data=extra_data)
        else:
            raise ValueError("Sin track")
    except Exception as e:
        print(f"Upload con música falló ({e}), subiendo sin música...")
        media = cl.clip_upload(Path(video_path), caption=caption)

    print(f"Reel publicado! ID: {media.pk}")
    return media.pk
