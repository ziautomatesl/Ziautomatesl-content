import edge_tts
import asyncio


async def _generate(text, audio_path):
    communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural", rate="+5%", pitch="-5Hz")
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
    """
    Fallback: distribute words evenly across the audio duration.
    Used when edge-tts doesn't emit WordBoundary events.
    """
    words = text.split()
    if not words:
        return []
    # Leave ~4% silence at start/end
    pad   = duration * 0.04
    total = duration - 2 * pad
    wdur  = total / len(words)
    return [
        {
            "word":  w,
            "start": pad + i * wdur,
            "end":   pad + i * wdur + wdur * 0.88,
        }
        for i, w in enumerate(words)
    ]


def create_audio(text, audio_path="zia_audio.mp3"):
    timings = asyncio.run(_generate(text, audio_path))

    if not timings:
        print("WordBoundary no disponible, estimando timings...")
        # Get duration from the generated audio
        from moviepy import AudioFileClip
        try:
            dur = AudioFileClip(audio_path).duration
        except Exception:
            dur = len(text.split()) * 0.45   # rough estimate
        timings = _estimate_timings(text, dur)

    print(f"Palabras detectadas: {len(timings)}")
    return audio_path, timings
