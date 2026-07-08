import json
import requests
from agents.config import GEMINI_API_KEY, get_template, SENDER_NAME

WA_LINK = "https://wa.me/34675082562?text=Hola%2C%20he%20recibido%20vuestro%20email%20y%20me%20interesa%20saber%20m%C3%A1s%20sobre%20ziautomate"


def generate_email(lead: dict) -> dict:
    tmpl = get_template(lead.get("sector", ""))
    if GEMINI_API_KEY:
        result = _gemini(lead, tmpl)
        if result:
            result["html"] = _build_html(result["body"], lead)
            return result
    base = _template(lead, tmpl)
    base["html"] = _build_html(base["body"], lead)
    return base


def _gemini(lead: dict, tmpl: dict) -> dict | None:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
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
- Termina con una pregunta para agendar 20 minutos (sin el botón, eso lo ponemos nosotros)
- NO uses palabras como "increíble", "revolucionario", "transformar", "potenciar"
- NO uses emojis en el cuerpo
- NO incluyas firma ni footer, solo el cuerpo del mensaje

Devuelve SOLO un JSON válido con este formato exacto:
{{"subject": "asunto aquí", "body": "cuerpo aquí sin firma ni footer"}}"""

    try:
        resp = requests.post(
            url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15
        )
        data = resp.json()
        if "error" in data:
            print(f"    Gemini API error {data['error'].get('code')}: {data['error'].get('message', '')[:120]}")
            return None
        text = data["candidates"][0]["content"]["parts"][0]["text"]
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

¿Tenéis 20 minutos esta semana para que os cuente cómo funcionaría exactamente para {negocio}?"""

    return {"subject": subject, "body": body}


def _build_html(body_text: str, lead: dict) -> str:
    # Estilo "email personal": sin cabecera, sin botón, sin tarjeta.
    # Parece escrito a mano desde Gmail — mejor entrega y más respuestas.
    paragraphs = "".join(
        f"<p style='margin:0 0 14px 0;'>{p.strip()}</p>"
        for p in body_text.strip().split("\n\n") if p.strip()
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#ffffff;">
  <div style="max-width:560px;margin:0 auto;padding:24px 20px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#222222;">

    {paragraphs}

    <p style="margin:0 0 14px 0;">Si te viene mejor por WhatsApp, escríbeme aquí:
      <a href="{WA_LINK}" style="color:#1a6bff;">wa.me/34675082562</a></p>

    <p style="margin:24px 0 2px 0;">Un saludo,</p>
    <p style="margin:0;font-weight:bold;">Zia</p>
    <p style="margin:0;color:#555555;">ziautomate — automatización para negocios locales</p>
    <p style="margin:0;color:#555555;">675 082 562 · <a href="https://ziautomate.netlify.app" style="color:#1a6bff;">ziautomate.netlify.app</a></p>

    <p style="margin:28px 0 0 0;font-size:12px;color:#999999;">
      Si no quieres recibir más emails, responde con "No gracias" y no te vuelvo a escribir.
    </p>

  </div>
</body>
</html>"""
