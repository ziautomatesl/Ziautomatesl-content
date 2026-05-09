from datetime import date
from scripts_bank import SCRIPTS


def _build_instagram_caption(script: str, engagement_question: str, hashtags: list) -> str:
    raw = script.replace("¿", "\n¿").replace("? ", "?\n").replace(". ", ".\n")
    sentences = [s.strip() for s in raw.split("\n") if s.strip()]

    hook = sentences[0] if sentences else ""
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
    first_line = f"{topic} | Automatización e IA para negocios"
    keywords = "automatizacion negocios inteligencia artificial pymes españa make n8n zapier business automation AI"
    hashtags_str = " ".join(hashtags)

    return (
        f"{first_line}\n\n"
        f"{script}\n\n"
        f"👉 Automatiza tu negocio → https://ziautomate.netlify.app\n\n"
        f"📲 Instagram: @ziautomate\n\n"
        f"{keywords}\n\n"
        f"{hashtags_str}"
    )


def _build_youtube_title(topic: str) -> str:
    if len(topic) <= 70:
        return f"{topic} | ziautomate"
    return topic[:97] + "..."


def generate_script(slot_number: int = 0) -> dict:
    """
    slot_number: 0 = YouTube 17:30 | 1 = Instagram 18:30 | 2 = Prime time 20:00
    Cada slot usa un script diferente del mismo día (3 scripts/día, ciclo de 10 días).
    """
    day_of_year = date.today().timetuple().tm_yday
    slot_index = (day_of_year * 3 + slot_number) % len(SCRIPTS)

    script_data = SCRIPTS[slot_index]

    hashtags     = script_data.get("hashtags", ["#automatizacion", "#ia", "#pymes", "#negocio", "#ziautomate"])
    eng_question = script_data.get("engagement_question", "¿Qué automatizarías primero en tu negocio?")

    instagram_caption   = _build_instagram_caption(script_data["script"], eng_question, hashtags)
    youtube_title       = _build_youtube_title(script_data["topic"])
    youtube_description = _build_youtube_description(script_data["topic"], script_data["script"], hashtags)
    youtube_tags        = [h.lstrip("#") for h in hashtags] + [
        "automatizacion", "inteligencia artificial", "pymes", "negocio digital", "españa"
    ]

    return {
        "topic":               script_data["topic"],
        "script":              script_data["script"],
        "highlights":          script_data.get("highlights", []),
        "engagement_question": eng_question,
        "instagram_caption":   instagram_caption,
        "youtube_title":       youtube_title,
        "youtube_description": youtube_description,
        "youtube_tags":        youtube_tags,
        "hashtags":            " ".join(hashtags),
    }
