import os
import json
import base64
import random
import subprocess
import tempfile
import urllib.request
from pathlib import Path


def _make_thumbnail(video_path: str) -> str:
    tmp = tempfile.mktemp(suffix=".jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-q:v", "2", tmp],
        capture_output=True,
    )
    return tmp


def _download_audio(cl, track) -> str | None:
    url = getattr(track, "_audio_url", None) or getattr(track, "progressive_download_url", None)
    if not url:
        return None
    tmp = tempfile.mktemp(suffix=".mp3")
    try:
        req = urllib.request.Request(str(url), headers={
            "User-Agent": "Instagram 219.0.0.12.117 Android",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) > 1000:
            with open(tmp, "wb") as f:
                f.write(data)
            print(f"Audio descargado: {len(data)} bytes")
            return tmp
        print(f"Audio vacío ({len(data)} bytes), sin audio.")
    except Exception as e:
        print(f"No se pudo descargar audio: {e}")
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
        "-af", "afade=t=in:d=1,afade=t=out:st=22:d=2",
        out,
    ], capture_output=True)
    if r.returncode == 0 and os.path.exists(out):
        print("Audio mezclado en el vídeo.")
        return out
    print("ffmpeg mix falló, subiendo sin audio.")
    return video_path


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
                    # Buscar URL de audio en el raw response
                    mai = track_data.get("music_asset_info") or {}
                    audio_url = (
                        track_data.get("progressive_download_url")
                        or mai.get("progressive_download_url")
                        or mai.get("audio_asset_url")
                        or track_data.get("preview_url")
                    )
                    track._audio_url = audio_url  # guardar en el objeto
                    print(f"Música: '{track.title}' – {track.display_artist} | audio_url: {'sí' if audio_url else 'no'}")
                    return track
                except Exception:
                    continue
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

    # Descargar audio y mezclarlo en el vídeo para que suene de verdad
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

    thumbnail = _make_thumbnail(upload_path)

    print("Subiendo Reel a Instagram...")
    try:
        if track:
            extra_data = cl.clip_music_extra_data(
                track=track,
                original_volume=1.0,
                music_volume=0.0,
            )
            media = cl.clip_upload(Path(upload_path), caption=caption, thumbnail=Path(thumbnail), extra_data=extra_data)
        else:
            media = cl.clip_upload(Path(upload_path), caption=caption, thumbnail=Path(thumbnail))
    except Exception as e:
        print(f"Upload falló ({e}), reintentando sin music_extra_data...")
        media = cl.clip_upload(Path(upload_path), caption=caption, thumbnail=Path(thumbnail))

    for f in [thumbnail, audio_tmp, mixed_tmp]:
        try:
            if f and os.path.exists(f):
                os.remove(f)
        except Exception:
            pass

    print(f"Reel publicado! ID: {media.pk}")
    return media.pk
