import os
import json
import base64
import time
import random
from pathlib import Path

POLL_OPTIONS = [
    ("¿Tu negocio responde de noche?",    ["Sí, siempre 💪",  "No, lo pierdo 😬"]),
    ("¿Cuántos clientes pierdes sin IA?", ["Demasiados 😅",   "Casi ninguno 🤷"]),
    ("¿Respondes mensajes a las 3am?",    ["Claro que no 😴", "A veces... 👀"]),
    ("¿Tu competencia ya usa IA?",        ["Seguro que sí",   "Todavía no"]),
    ("¿Automatizarías tu negocio hoy?",   ["100% sí 🔥",      "Tengo dudas"]),
    ("¿Cuánto vale 1 cliente perdido?",   ["Mucho dinero 💸", "No lo sé"]),
]

MUSIC_QUERIES = ["phonk", "trap motivation", "dark trap", "motivacional", "hustle", "viral"]


def get_track(cl):
    from instagrapi.extractors import extract_track as _extract_track
    random.shuffle(MUSIC_QUERIES)
    for query in MUSIC_QUERIES:
        try:
            result = cl.private_request(
                "music/audio_global_search/",
                params={"query": query, "browse_session_id": cl.generate_uuid()},
            )
            for item in (result or {}).get("items") or []:
                if not item or not isinstance(item, dict):
                    continue
                track_data = item.get("track")
                if not track_data or not isinstance(track_data, dict):
                    continue
                try:
                    track = _extract_track(track_data)
                    print(f"Música story: '{track.title}' – {track.display_artist}")
                    return track
                except Exception:
                    continue
        except Exception as e:
            print(f"Error buscando música ({query}): {e}")
    return None


def post_instagram_story(video_path: str, poll_index: int = -1) -> str:
    from instagrapi import Client
    from instagrapi.types import StoryPoll, StoryLink

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
    time.sleep(4)

    # Encuesta rotativa
    idx = poll_index % len(POLL_OPTIONS) if poll_index >= 0 else random.randint(0, len(POLL_OPTIONS) - 1)
    question, options = POLL_OPTIONS[idx]
    poll = StoryPoll(x=0.5, y=0.82, width=0.72, height=0.14, rotation=0.0, question=question, options=options)
    print(f"Encuesta: '{question}' → {options}")

    # Link directo al DM
    link = StoryLink(webUri="https://ig.me/m/ziautomate")

    # Track de Instagram para la story
    track = get_track(cl)

    path = Path(video_path)
    print(f"Subiendo Story: {path.name}")

    # Intento 1: música solo metadata (sin mezcla local), encuesta + link
    if track:
        try:
            music_extra = cl.story_music_extra_data(
                track,
                original_volume=0.0,
                music_volume=1.0,
            )
            media = cl.video_upload_to_story(
                path=path,
                caption="",
                links=[link],
                polls=[poll],
                extra_data=music_extra,
            )
            print(f"Story publicada con música! ID: {media.pk}")
            return media.pk
        except Exception as e:
            print(f"Story con música falló: {e}")

    # Intento 2: sin música, con encuesta + link
    try:
        media = cl.video_upload_to_story(
            path=path,
            caption="",
            links=[link],
            polls=[poll],
        )
        print(f"Story publicada (sin música)! ID: {media.pk}")
        return media.pk
    except Exception as e:
        print(f"Story con link falló: {e}")

    # Intento 3: mínimo — solo encuesta
    media = cl.video_upload_to_story(path=path, caption="", polls=[poll])
    print(f"Story publicada (solo encuesta)! ID: {media.pk}")
    return media.pk
