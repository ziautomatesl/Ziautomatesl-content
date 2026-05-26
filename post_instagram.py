import os
import json
import base64
import random

MUSIC_QUERIES = ["phonk", "trap motivation", "dark trap", "motivacional", "hustle beats"]


def get_track(cl):
    try:
        tracks = cl.search_music(random.choice(MUSIC_QUERIES))
        if tracks:
            track = random.choice(tracks[:8])
            print(f"Música reel: '{track.title}' – {track.display_artist}")
            return track
    except Exception as e:
        print(f"Música no disponible: {e}")
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
            media = cl.clip_upload_as_reel_with_music(video_path, caption=caption, track=track)
        else:
            raise Exception("Sin track")
    except Exception as e:
        print(f"Upload con música falló ({e}), subiendo sin música...")
        media = cl.clip_upload(video_path, caption=caption)

    print(f"Reel publicado! ID: {media.pk}")
    return media.pk
