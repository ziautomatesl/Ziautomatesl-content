import os
import json
import base64
import time
import random
import subprocess
import tempfile
from pathlib import Path


def _download_audio(cl, track) -> str | None:
    url = getattr(track, "_audio_url", None) or getattr(track, "progressive_download_url", None)
    if not url:
        return None
    try:
        tmp = tempfile.mktemp(suffix=".mp3")
        resp = cl.private.get(str(url), timeout=20, stream=True)
        if resp.status_code == 200:
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return tmp
    except Exception as e:
        print(f"No se pudo descargar audio story: {e}")
    return None


def _mix_audio(video_path: str, audio_path: str) -> str:
    out = video_path.replace(".mp4", "_m.mp4")
    r = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-af", "afade=t=in:d=1,afade=t=out:st=8:d=2",
        out,
    ], capture_output=True)
    if r.returncode == 0 and os.path.exists(out):
        print("Audio mezclado en story.")
        return out
    return video_path

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
                    mai = track_data.get("music_asset_info") or {}
                    audio_url = (
                        track_data.get("progressive_download_url")
                        or mai.get("progressive_download_url")
                        or mai.get("audio_asset_url")
                        or track_data.get("preview_url")
                    )
                    track._audio_url = audio_url
                    print(f"Música story: '{track.title}' – {track.display_artist} | audio: {'sí' if audio_url else 'no'}")
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
    poll = StoryPoll(x=0.5, y=0.73, width=0.70, height=0.14, rotation=0.0, question=question, options=options)
    print(f"Encuesta: '{question}' → {options}")

    # Link directo al DM
    link = StoryLink(webUri="https://ig.me/m/ziautomate")

    # Track de Instagram para la story
    track = get_track(cl)

    # Mezclar audio en el vídeo si tenemos track
    upload_path = video_path
    audio_tmp = None
    mixed_tmp = None
    if track:
        audio_tmp = _download_audio(cl, track)
        if audio_tmp:
            mixed = _mix_audio(video_path, audio_tmp)
            if mixed != video_path:
                mixed_tmp = mixed
                upload_path = mixed_tmp

    path = Path(upload_path)
    print(f"Subiendo Story: {path.name}")

    try:
        media = cl.video_upload_to_story(
            path=path,
            caption="",
            links=[link],
            polls=[poll],
        )
        print(f"Story publicada! ID: {media.pk}")
    except Exception as e:
        print(f"Story con link/poll falló ({e}), solo encuesta...")
        media = cl.video_upload_to_story(path=path, caption="", polls=[poll])
        print(f"Story publicada (solo encuesta)! ID: {media.pk}")

    for f in [audio_tmp, mixed_tmp]:
        try:
            if f and os.path.exists(f):
                os.remove(f)
        except Exception:
            pass

    return media.pk
