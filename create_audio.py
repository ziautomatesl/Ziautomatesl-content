import edge_tts
import asyncio
import re

VOICE = "es-ES-AlvaroNeural"
RATE  = "+5%"


async def _generate(text, audio_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    word_timings   = []
    chunk_types    = set()

    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            chunk_types.add(chunk["type"])
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                start    = chunk["offset"]  / 10_000_000
                duration = chunk["duration"] / 10_000_000
                word_timings.append({
                    "word":        chunk["text"],
                    "start":       start,
                    "end":         start + duration,
                    "is_sentence": chunk["type"] == "SentenceBoundary",
                })

    print(f"Tipos de chunks recibidos: {chunk_types}")
    return word_timings


def _expand_sentences(sentence_timings):
    """
    If we only got SentenceBoundary events, expand each sentence into
    individual words with proportional timing based on character count.
    """
    result = []
    for st in sentence_timings:
        sent_dur = st["end"] - st["start"]
        words    = st["word"].split()
        if not words:
            continue
        lens  = [max(1, len(w.strip(".,;:¿?!¡—–"))) for w in words]
        total = sum(lens)
        t = st["start"]
        for w, c in zip(words, lens):
            wdur = sent_dur * c / total
            result.append({"word": w, "start": t, "end": t + wdur * 0.90})
            t += wdur
    return result


def _estimate_timings(text: str, duration: float):
    """
    No timing events at all — distribute by natural phrase boundaries.
    Splits at sentence-ending punctuation first, then proportional by chars.
    """
    # Split into sentences
    raw_sents = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in raw_sents if s.strip()]
    if not sentences:
        sentences = [text.strip()]

    lens   = [max(1, len(s)) for s in sentences]
    total  = sum(lens)
    pad    = duration * 0.02
    usable = duration - 2 * pad

    result = []
    t = pad
    for sent, slen in zip(sentences, lens):
        sent_dur = usable * slen / total
        words = sent.split()
        if not words:
            t += sent_dur
            continue
        wlens    = [max(1, len(w.strip(".,;:¿?!¡—–"))) for w in words]
        wtotal   = sum(wlens)
        for w, c in zip(words, wlens):
            wdur = sent_dur * c / wtotal
            result.append({"word": w, "start": t, "end": t + wdur * 0.88})
            t += wdur

    return result


def _scale_timings(timings, scale):
    return [{"word": t["word"], "start": t["start"] * scale, "end": t["end"] * scale}
            for t in timings]


def create_audio(text, audio_path="zia_audio.mp3"):
    raw = asyncio.run(_generate(text, audio_path))

    from moviepy import AudioFileClip
    try:
        clip = AudioFileClip(audio_path)
        audio_duration = clip.duration
        clip.close()
    except Exception:
        audio_duration = len(text.split()) * 0.45

    print(f"Duración audio: {audio_duration:.3f}s")

    if not raw:
        print("Sin eventos de timing — estimando por pausas naturales...")
        timings = _estimate_timings(text, audio_duration)

    elif all(t["is_sentence"] for t in raw):
        print(f"Solo SentenceBoundary ({len(raw)} frases) — expandiendo a palabras...")
        timings = _expand_sentences(raw)

    else:
        # Word-level events received
        timings = [{"word": t["word"], "start": t["start"], "end": t["end"]} for t in raw]
        print(f"WordBoundary recibidos: {len(timings)} palabras")
        print(f"  1ª: '{timings[0]['word']}' @ {timings[0]['start']:.3f}s")
        print(f"  última: '{timings[-1]['word']}' @ {timings[-1]['end']:.3f}s")

        last_end = timings[-1]["end"]
        ratio    = last_end / audio_duration if audio_duration > 0 else 1.0
        print(f"  ratio timings/audio: {ratio:.3f}")
        if ratio > 1.08:
            scale = (audio_duration * 0.97) / last_end
            print(f"  → Aplicando corrección escala: {scale:.4f}")
            timings = _scale_timings(timings, scale)

    print(f"Palabras detectadas: {len(timings)}")
    return audio_path, timings
