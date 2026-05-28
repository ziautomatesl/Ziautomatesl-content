import os
import json
import subprocess
import urllib.request
import urllib.parse

_HERE        = os.path.dirname(os.path.abspath(__file__))
REMOTION_DIR = os.path.join(_HERE, "remotion")

PEXELS_QUERIES = {
    "automatizacion": "business automation technology",
    "clientes":       "business customer service",
    "ventas":         "sales business growth",
    "whatsapp":       "smartphone communication business",
    "ia":             "artificial intelligence technology",
    "horas":          "productivity work time",
    "redes":          "social media content creation",
    "cobros":         "business finance invoice",
    "formulario":     "web business lead",
    "n8n":            "technology automation workflow",
    "default":        "modern business professional",
}


def _pexels_query(topic: str) -> str:
    t = topic.lower()
    for kw, q in PEXELS_QUERIES.items():
        if kw in t:
            return q
    return PEXELS_QUERIES["default"]


def fetch_pexels_photos(topic: str, count: int = 6, suffix: str = "dynamic") -> bool:
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        print("PEXELS_API_KEY no configurado, usando fotos estáticas.")
        return False

    query = _pexels_query(topic)
    photos_dir = os.path.join(REMOTION_DIR, "public", "photos")
    os.makedirs(photos_dir, exist_ok=True)

    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={count}&orientation=portrait"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        photos = data.get("photos", [])
        if not photos:
            print(f"Pexels sin resultados para '{query}', usando fotos estáticas.")
            return False
        for i, photo in enumerate(photos[:count]):
            img_url = photo["src"]["portrait"]
            dest = os.path.join(photos_dir, f"{suffix}_{i}.jpg")
            urllib.request.urlretrieve(img_url, dest)
        print(f"Fotos Pexels descargadas: {len(photos[:count])} ({query})")
        return True
    except Exception as e:
        print(f"Pexels error ({e}), usando fotos estáticas.")
        return False


def create_carousel_video(content: dict, output_path: str = "zia_video.mp4") -> str:
    fetch_pexels_photos(content.get("topic", ""), count=6, suffix="carousel")
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
    fetch_pexels_photos(content.get("topic", ""), count=1, suffix="story")
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

    # Split question into exactly 2 lines of max 3 words each
    words = eng_q.split()
    hook_line1 = " ".join(words[:3])
    hook_line2 = " ".join(words[3:6]) if len(words) > 3 else topic.split()[0]

    # Stat
    stat_number, stat_suffix = 78, "%"
    for h in highlights:
        m = re.search(r"(\d+)\s*(%|X|x)", h)
        if m:
            stat_number = int(m.group(1))
            stat_suffix = m.group(2).upper()
            break

    # Stat label: first complete sentence of script, max 60 chars at word boundary
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', script) if len(s.strip()) > 10]
    raw = sentences[0] if sentences else "de las ventas va al negocio que responde primero."
    if len(raw) > 60:
        raw = raw[:60].rsplit(" ", 1)[0] + "…"
    stat_label = raw

    # Photo rotates daily (1-6)
    photo_index = (date.today().toordinal() % 6) + 1

    return {
        "hook_label":  "PREGUNTA DEL DÍA",
        "hook_line1":  hook_line1,
        "hook_line2":  hook_line2,
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
