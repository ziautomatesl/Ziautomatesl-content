import edge_tts
import asyncio

VOICE = "es-ES-AlvaroNeural"
RATE  = "+5%"


async def _generate(text, audio_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    word_timings = []

    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start    = chunk["offset"]  / 10_000_000
                duration = chunk["duration"] / 10_000_000
                word_timings.append({
                    "word":  chunk["text"],
                    "start": start,
                    "end":   start + duration,
                })

    return word_timings


def _estimate_timings(text: str, duration: float):
    words = text.split()
    if not words:
        return []
    pad   = duration * 0.04
    total = duration - 2 * pad
    # Weight by character length (longer words = more time)
    lens  = [max(1, len(w.strip(".,;:¿?!¡"))) for w in words]
    total_chars = sum(lens)
    timings = []
    t = pad
    for w, c in zip(words, lens):
        wdur = total * c / total_chars
        timings.append({"word": w, "start": t, "end": t + wdur * 0.88})
        t += wdur
    return timings


def _scale_timings(timings, scale):
    return [{"word": t["word"], "start": t["start"] * scale, "end": t["end"] * scale}
            for t in timings]


def create_audio(text, audio_path="zia_audio.mp3"):
    timings = asyncio.run(_generate(text, audio_path))

    # Get real audio duration for calibration
    from moviepy import AudioFileClip
    try:
        clip = AudioFileClip(audio_path)
        audio_duration = clip.duration
        clip.close()
    except Exception:
        audio_duration = len(text.split()) * 0.45

    print(f"Duración audio: {audio_duration:.3f}s")

    if not timings:
        print("WordBoundary no disponible — estimando timings...")
        timings = _estimate_timings(text, audio_duration)
    else:
        last_end = timings[-1]["end"]
        print(f"Timings edge-tts: {len(timings)} palabras")
        print(f"  1ª: '{timings[0]['word']}' @ {timings[0]['start']:.3f}s")
        print(f"  última: '{timings[-1]['word']}' @ {last_end:.3f}s")
        print(f"  ratio timings/audio: {last_end/audio_duration:.3f}")

        # If timings extend significantly past audio duration the timestamps
        # are not rate-adjusted — scale them down to fit the actual audio.
        if audio_duration > 0 and last_end > audio_duration * 1.08:
            scale = (audio_duration * 0.97) / last_end
            print(f"  → Aplicando corrección de escala: {scale:.4f}")
            timings = _scale_timings(timings, scale)

    print(f"Palabras detectadas: {len(timings)}")
    return audio_path, timings
