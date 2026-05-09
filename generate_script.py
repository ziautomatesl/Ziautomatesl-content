from datetime import date
from scripts_bank import SCRIPTS


def _build_instagram_caption(script: str, engagement_question: str, hashtags: list) -> str:
    # Split script into sentences
    raw = script.replace("¿", "\n¿").replace("? ", "?\n").replace(". ", ".\n")
    sentences = [s.strip() for s in raw.split("\n") if s.strip()]

    # Hook = primera oración (para antes del "ver más" — máx ~150 chars)
    hook = sentences[0] if sentences else ""

    # Cuerpo = las siguientes 2-3 oraciones
    body_lines = sentences[1:4] if len(sentences) > 1 else []
    body = "\n".join(body_lines)

    hashtags_str = " ".join(hashtags)

    return (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"{engagement_question}\n\n"
        f"🔗 ziautomate.netlify.app\n\n"
        f"{hashtags_str}"
    )


def _build_youtube_description(topic: str, script: str, hashtags: list) -> str:
    # Primera línea: keyword principal + promesa (para el buscador de YouTube)
    first_line = f"{topic} | Automatización e IA para negocios"

    # Cuerpo: el guion completo
    body = script

    # Keywords para el buscador (en español + inglés para más alcance)
    keywords = "automatizacion negocios inteligencia artificial pymes españa make n8n zapier business automation AI"

    hashtags_str = " ".join(hashtags)

    return (
        f"{first_line}\n\n"
        f"{body}\n\n"
        f"👉 Automatiza tu negocio → https://ziautomate.netlify.app\n\n"
        f"📲 Instagram: @ziautomate\n\n"
        f"{keywords}\n\n"
        f"{hashtags_str}"
    )


def _build_youtube_title(topic: str) -> str:
    # Título SEO: el topic ya es bueno, añadimos gancho de resultado si cabe en 100 chars
    if len(topic) <= 70:
        return f"{topic} | ziautomate"
    return topic[:97] + "..."


def generate_script(slot: str = "morning") -> dict:
    day_of_year = date.today().timetuple().tm_yday

    # Mañana y tarde usan scripts distintos del mismo día
    offset = 0 if slot == "morning" else 1
    slot_index = (day_of_year * 2 + offset) % len(SCRIPTS)

    script_data = SCRIPTS[slot_index]

    hashtags        = script_data.get("hashtags", ["#automatizacion", "#ia", "#pymes", "#negocio", "#ziautomate"])
    eng_question    = script_data.get("engagement_question", "¿Qué automatizarías primero en tu negocio?")

    instagram_caption   = _build_instagram_caption(script_data["script"], eng_question, hashtags)
    youtube_title       = _build_youtube_title(script_data["topic"])
    youtube_description = _build_youtube_description(script_data["topic"], script_data["script"], hashtags)

    # Tags para la API de YouTube (sin #, máx 500 chars total)
    youtube_tags = [h.lstrip("#") for h in hashtags] + [
        "automatizacion", "inteligencia artificial", "pymes", "negocio digital", "españa"
    ]

    return {
        "topic":                script_data["topic"],
        "script":               script_data["script"],
        "highlights":           script_data.get("highlights", []),
        "instagram_caption":    instagram_caption,
        "youtube_title":        youtube_title,
        "youtube_description":  youtube_description,
        "youtube_tags":         youtube_tags,
        # legacy — por si algo lo usa todavía
        "hashtags":             " ".join(hashtags),
    }
