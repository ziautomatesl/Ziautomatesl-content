import os
import json
import base64
import time

def post_instagram_story(image_path: str) -> str:
    from instagrapi import Client

    username    = os.environ["INSTAGRAM_USERNAME"]
    password    = os.environ["INSTAGRAM_PASSWORD"]
    session_b64 = os.environ.get("INSTAGRAM_SESSION", "")

    cl = Client()
    cl.delay_range = [3, 7]

    if session_b64:
        try:
            session = json.loads(base64.b64decode(session_b64).decode())
            cl.set_settings(session)
        except Exception as e:
            print(f"Sesión inválida, login fresco: {e}")

    cl.login(username, password)

    # Small delay after login before posting story
    time.sleep(5)

    print("Subiendo Historia a Instagram...")
    media = cl.photo_upload_to_story(image_path)
    print(f"Historia publicada! ID: {media.pk}")
    return media.pk
