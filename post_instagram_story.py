import os
import json
import base64
import time


def post_instagram_story(image_path: str, question: str = "") -> str:
    from instagrapi import Client
    from instagrapi.types import StoryPoll

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
    time.sleep(5)

    polls = []
    if question:
        # Truncate question to 100 chars (Instagram limit)
        q = question[:100]
        poll = StoryPoll(
            x=0.5, y=0.75,
            width=0.9, height=0.14,
            rotation=0.0,
            question=q,
            options=["¡Sí!", "Aún no"],
        )
        polls.append(poll)
        print(f"Añadiendo encuesta nativa: '{q}'")

    print("Subiendo Historia a Instagram...")
    media = cl.photo_upload_to_story(image_path, polls=polls)
    print(f"Historia publicada! ID: {media.pk}")
    return media.pk
