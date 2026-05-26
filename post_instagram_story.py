import os
import json
import base64
import time
import random


POLL_OPTIONS = [
    ("¿Tu negocio responde de noche?",      ["Sí, siempre 💪",  "No, lo pierdo 😬"]),
    ("¿Cuántos clientes pierdes sin IA?",   ["Demasiados 😅",   "Casi ninguno 🤷"]),
    ("¿Respondes mensajes a las 3am?",      ["Claro que no 😴", "A veces... 👀"]),
    ("¿Tu competencia ya usa IA?",          ["Seguro que sí",   "Todavía no"]),
    ("¿Automatizarías tu negocio hoy?",     ["100% sí 🔥",      "Tengo dudas"]),
    ("¿Cuánto vale 1 cliente perdido?",     ["Mucho dinero 💸", "No lo sé"]),
]

MUSIC_QUERIES = [
    "phonk", "trap motivation", "dark trap", "motivational beats",
    "gym motivation", "hustle", "business", "viral beat",
]


def get_trending_track(cl):
    query = random.choice(MUSIC_QUERIES)
    try:
        tracks = cl.music_search(query)
        if tracks:
            track = random.choice(tracks[:8])
            print(f"Música: '{track.title}' – {track.artist_name} (id: {track.track_id})")
            return track
    except Exception as e:
        print(f"No se pudo obtener música trending: {e}")
    return None


def post_instagram_story(video_path: str, poll_index: int = -1) -> str:
    from instagrapi import Client
    from instagrapi.types import StoryPoll, StoryLink, StoryMusic

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

    # Poll — rotate by index or random
    idx = poll_index % len(POLL_OPTIONS) if poll_index >= 0 else random.randint(0, len(POLL_OPTIONS) - 1)
    question, options = POLL_OPTIONS[idx]
    poll = StoryPoll(
        x=0.5, y=0.72,
        width=0.88, height=0.14,
        rotation=0.0,
        question=question,
        options=options,
    )
    print(f"Encuesta: '{question}' → {options}")

    # Link sticker — DM directo
    link = StoryLink(webUri="https://ig.me/m/ziautomate")

    # Música trending
    stickers = []
    track = get_trending_track(cl)
    if track:
        try:
            music = StoryMusic(
                track_id=str(track.track_id),
                start_ms=0,
                end_ms=10000,
                x=0.5, y=0.92,
                width=0.9, height=0.1,
                rotation=0.0,
                display_type="lyrics" if hasattr(track, "has_lyrics") and track.has_lyrics else "full",
            )
            stickers.append(music)
        except Exception as e:
            print(f"Music sticker falló, sin música: {e}")

    print("Subiendo Story a Instagram...")
    media = cl.video_upload_to_story(
        path=video_path,
        caption="",
        links=[link],
        polls=[poll],
        music_stickers=stickers if stickers else None,
    )
    print(f"Story publicada! ID: {media.pk}")
    return media.pk
