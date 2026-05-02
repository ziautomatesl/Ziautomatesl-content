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
                start = chunk["offset"] / 10_000_000
                duration = chunk["duration"] / 10_000_000
                word_timings.append({
                    "word": chunk["text"],
                    "start": start,
                    "end": start + duration
                })

    return word_timings

def create_audio(text, audio_path="zia_audio.mp3"):
    timings = asyncio.run(_generate(text, audio_path))
    return audio_path, timings
