import os
import json
import subprocess

_HERE        = os.path.dirname(os.path.abspath(__file__))
REMOTION_DIR = os.path.join(_HERE, "remotion")


def create_carousel_video(content: dict, output_path: str = "zia_video.mp4") -> str:
    props = build_carousel_props(content)

    props_path = os.path.join(REMOTION_DIR, "props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    abs_output = os.path.abspath(output_path)
    print("Renderizando carrusel con Remotion...")
    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts", "ZiaCarousel",
            "--props",        "props.json",
            "--output",       abs_output,
            "--codec",        "h264",
            "--image-format", "jpeg",
            "--jpeg-quality", "95",
            "--concurrency",  "4",
        ],
        cwd=REMOTION_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )

    try:
        os.remove(props_path)
    except Exception:
        pass

    return output_path


def create_story_video(content: dict, output_path: str = "zia_story.mp4") -> str:
    props = build_story_props(content)

    props_path = os.path.join(REMOTION_DIR, "story_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    abs_output = os.path.abspath(output_path)
    print("Renderizando historia con Remotion...")
    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts", "ZiaStory",
            "--props",        "story_props.json",
            "--output",       abs_output,
            "--codec",        "h264",
            "--image-format", "jpeg",
            "--jpeg-quality", "95",
            "--concurrency",  "4",
        ],
        cwd=REMOTION_DIR,
        check=True,
        env={**os.environ, "CI": "true"},
    )

    try:
        os.remove(props_path)
    except Exception:
        pass

    return output_path


def build_story_props(content: dict) -> dict:
    if "story" in content:
        return content["story"]

    import re
    from datetime import date

    eng_q  = content.get("engagement_question", "¿Tu negocio trabaja mientras duermes?")
    topic  = content.get("topic", "Tu negocio 24/7")
    highlights = content.get("highlights", [])
    script = content.get("script", "")

    # Split question into 2 punchy lines (~3-4 words each)
    words = eng_q.split()
    mid = max(2, min(4, len(words) // 2))
    hook_line1 = " ".join(words[:mid])
    hook_line2 = " ".join(words[mid:]) if mid < len(words) else topic[:38]

    # Stat
    stat_number, stat_suffix = 78, "%"
    for h in highlights:
        m = re.search(r"(\d+)\s*(%|X|x)", h)
        if m:
            stat_number = int(m.group(1))
            stat_suffix = m.group(2).upper()
            break

    # Stat label: first sentence of script, max 65 chars
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', script) if len(s.strip()) > 10]
    stat_label = sentences[0][:65] if sentences else "de las ventas va al negocio que responde primero."

    # Photo rotates daily (1-6)
    photo_index = (date.today().toordinal() % 6) + 1

    return {
        "hook_label":  "PREGUNTA DEL DÍA",
        "hook_line1":  hook_line1[:38],
        "hook_line2":  hook_line2[:38],
        "hook_sub":    "Responde abajo — ¿cuánto te cuesta el silencio?",
        "stat_number": stat_number,
        "stat_suffix": stat_suffix,
        "stat_label":  stat_label,
        "photo_index": photo_index,
    }


def build_carousel_props(content: dict) -> dict:
    # Use explicit carousel field if provided in scripts_bank
    if "carousel" in content:
        return content["carousel"]

    topic     = content.get("topic", "Tu negocio 24/7")
    highlights = content.get("highlights", [])
    script    = content.get("script", "")
    eng_q     = content.get("engagement_question", "")

    # Extract stat number from highlights (e.g. "78% AL PRIMERO" → 78, "%")
    import re
    stat_number, stat_suffix = 67, "%"
    for h in highlights:
        m = re.search(r"(\d+)\s*(%|X|x)", h)
        if m:
            stat_number = int(m.group(1))
            stat_suffix = m.group(2).upper()
            break

    # Build proof bullets from highlights (clean them up)
    def clean_highlight(h: str) -> str:
        return h.replace("_", " ").title() + "."

    bullets = [clean_highlight(h) for h in highlights[:3]]
    while len(bullets) < 3:
        bullets.append("Resultados comprobados en 30 días.")

    # Split topic into vision hook (first half) and result (second half)
    words = topic.split()
    mid = max(1, len(words) // 2)
    hook = " ".join(words[:mid])
    result = " ".join(words[mid:]) if mid < len(words) else topic

    # Stat context from script (first sentence before any number)
    sentences = [s.strip() for s in re.split(r'(?<=[.?])\s+', script) if len(s.strip()) > 15]
    stat_context = sentences[2] if len(sentences) > 2 else f"de los negocios {topic.lower()}"
    stat_footnote = sentences[3] if len(sentences) > 3 else eng_q[:80]

    return {
        "topic":          topic,
        "tag":            "Automatización IA",
        "stat_number":    stat_number,
        "stat_suffix":    stat_suffix,
        "stat_context":   stat_context[:80],
        "stat_footnote":  stat_footnote[:80],
        "solution_line1": "Una IA que",
        "solution_line2": "trabaja por ti.",
        "solution_word1": "Responde.",
        "solution_word2": "Convierte.",
        "solution_sub":   "Automático. Las 24 horas.",
        "vision_hook":    f"{hook}.",
        "vision_result":  f"{result}.",
        "vision_body":    "Tu negocio funcionando mientras dormías.",
        "vision_brand":   "Eso es ziautomate.",
        "bullet1":        bullets[0],
        "bullet2":        bullets[1],
        "bullet3":        bullets[2],
        "cta_sub":        "Sin empleados extra. Sin estrés.",
        "cta_button":     "Activa tu negocio 24/7",
    }
