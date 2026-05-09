import json
import requests
from agents.config import GEMINI_API_KEY, get_template, SENDER_NAME


def generate_email(lead: dict) -> dict:
    tmpl = get_template(lead.get("sector", ""))
    if GEMINI_API_KEY:
        result = _gemini(lead, tmpl)
        if result:
            return result
    return _template(lead, tmpl)


def _gemini(lead: dict, tmpl: dict) -> dict | None:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    prompt = f"""Eres experto en cold email para PYMEs españolas. Escribe un email de prospección breve y personal.

Datos del negocio:
- Nombre: {lead['negocio']}
- Sector: {lead['sector']}
- Ciudad: {lead['ciudad']}

Contexto ziautomate:
- Dolor del sector: {tmpl['pain']}
- Solución: {tmpl['solution']}
- Caso de éxito: {tmpl['case_study']}

Reglas estrictas:
- Tono directo, cercano, humano — como si fuera una persona real escribiendo
- Cuerpo máximo 120 palabras
- Menciona el nombre exacto del negocio en el primer párrafo
- Termina pidiendo 20 minutos de llamada o videollamada
- NO uses palabras como "increíble", "revolucionario", "transformar", "potenciar"
- NO uses emojis en el cuerpo (sí en la firma)
- Firma exacta: {SENDER_NAME} | 675 082 562 | ziautomate.netlify.app | @ziautomate.sl
- Footer: "ziautomate S.L. · Madrid · Si no deseas recibir más emails, responde con 'No gracias'"

Devuelve SOLO un JSON válido con este formato exacto:
{{"subject": "asunto aquí", "body": "cuerpo completo aquí"}}"""

    try:
        resp = requests.post(
            url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15
        )
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        print(f"    Gemini error: {e}")
        return None


def _template(lead: dict, tmpl: dict) -> dict:
    negocio = lead.get("negocio", "")
    ciudad  = lead.get("ciudad", "")

    subject = f"{negocio}: {tmpl['stat']}"

    body = f"""Hola,

He visto que {negocio} está en {ciudad} y quería escribiros directamente.

La mayoría de negocios de vuestro sector pierden tiempo y dinero por {tmpl['pain']} — sin darse cuenta.

{tmpl['case_study']}

Lo que hacemos en ziautomate es {tmpl['solution']}, sin que tengáis que cambiar nada de cómo trabajáis.

¿Tenéis 20 minutos esta semana para que os explique cómo funcionaría exactamente para {negocio}?

Un saludo,
ziautomate | 675 082 562 | ziautomate.netlify.app | @ziautomate.sl

---
ziautomate S.L. · Madrid, España
Si no deseas recibir más emails, responde con "No gracias"."""

    return {"subject": subject, "body": body}
