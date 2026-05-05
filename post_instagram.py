import os
import json
import base64

def post_instagram(video_path, caption):
    from instagrapi import Client

    username = os.environ["INSTAGRAM_USERNAME"]
    password = os.environ["INSTAGRAM_PASSWORD"]
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

    print("Subiendo Reel a Instagram...")
    media = cl.clip_upload(video_path, caption=caption)
    print(f"Publicado en Instagram! ID: {media.pk}")
    return media.pk
