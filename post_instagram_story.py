import os
import json
import base64
import time
import random

POLL_OPTIONS = [
    ("¿Tu negocio responde de noche?",    ["Sí, siempre 💪",  "No, lo pierdo 😬"]),
    ("¿Cuántos clientes pierdes sin IA?", ["Demasiados 😅",   "Casi ninguno 🤷"]),
    ("¿Respondes mensajes a las 3am?",    ["Claro que no 😴", "A veces... 👀"]),
    ("¿Tu competencia ya usa IA?",        ["Seguro que sí",   "Todavía no"]),
    ("¿Automatizarías tu negocio hoy?",   ["100% sí 🔥",      "Tengo dudas"]),
    ("¿Cuánto vale 1 cliente perdido?",   ["Mucho dinero 💸", "No lo sé"]),
]

MUSIC_QUERIES = ["phonk", "trap motivation", "dark trap", "motivational", "hustle beats", "viral beat"]


def get_trending_track(cl):
    query = random.choice(MUSIC_QUERIES)
    try:
        tracks = cl.search_music(query)
        if tracks:
            track = random.choice(tracks[:8])
            print(f"Música: '{track.title}' – {track.display_artist} (id: {track.id})")
            return track
    except Exception as e:
        print(f"No se pudo obtener música: {e}")
    return None


def login_client():
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
    time.sleep(5)
    return cl


def post_instagram_story(video_path: str, poll_index: int = -1) -> str:
    from instagrapi.types import StoryPoll, StoryLink

    cl = login_client()

    # Poll rotativo
    idx = poll_index % len(POLL_OPTIONS) if poll_index >= 0 else random.randint(0, len(POLL_OPTIONS) - 1)
    question, options = POLL_OPTIONS[idx]
    poll = StoryPoll(x=0.5, y=0.72, width=0.88, height=0.14, rotation=0.0, question=question, options=options)
    print(f"Encuesta: '{question}' → {options}")

    # Link al DM
    link = StoryLink(webUri="https://ig.me/m/ziautomate")

    # Música trending
    track = get_trending_track(cl)

    print("Subiendo Story a Instagram...")
    try:
        if track:
            media = cl.video_upload_to_story_with_music(
                path=video_path,
                caption="",
                track=track,
                links=[link],
                polls=[poll],
                original_volume=0.0,
                music_volume=1.0,
            )
        else:
            raise Exception("Sin track, usando upload normal")
    except Exception as e:
        print(f"Upload con música falló ({e}), subiendo sin música...")
        try:
            media = cl.video_upload_to_story(
                path=video_path,
                caption="",
                links=[link],
                polls=[poll],
            )
        except Exception as e2:
            print(f"Upload con link falló ({e2}), subiendo solo con encuesta...")
            media = cl.video_upload_to_story(path=video_path, caption="", polls=[poll])

    print(f"Story publicada! ID: {media.pk}")
    return media.pk
