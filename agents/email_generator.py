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

¿Tenéis 20 minutos esta semana para que os cuente cómo funcionaría exactamente para {negocio}?"""

    return {"subject": subject, "body": body}


def _build_html(body_text: str, lead: dict) -> str:
    paragraphs = "".join(
        f"<p style='margin:0 0 16px 0;'>{p.strip()}</p>"
        for p in body_text.strip().split("\n\n") if p.strip()
    )
    negocio = lead.get("negocio", "")

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:32px 0;">
    <tr><td align="center">
      <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#00e5ff 0%,#1a6bff 50%,#7c3aed 100%);padding:28px 40px;">
            <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">ziautomate</span>
            <span style="font-size:13px;color:rgba(255,255,255,.75);margin-left:10px;">Tu negocio en piloto automático</span>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px 24px;color:#1f2937;font-size:15px;line-height:1.7;">
            {paragraphs}
          </td>
        </tr>

        <!-- CTA Button -->
        <tr>
          <td align="center" style="padding:8px 40px 36px;">
            <a href="{WA_LINK}" target="_blank"
               style="display:inline-block;background:linear-gradient(135deg,#1a6bff,#7c3aed);color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;padding:14px 32px;border-radius:8px;letter-spacing:0.2px;">
              Me interesa — escribir por WhatsApp
            </a>
          </td>
        </tr>

        <!-- Firma -->
        <tr>
          <td style="padding:0 40px 28px;border-top:1px solid #f0f0f0;">
            <p style="margin:20px 0 4px;font-size:14px;color:#374151;font-weight:600;">ziautomate</p>
            <p style="margin:0;font-size:13px;color:#6b7280;">675 082 562 &nbsp;·&nbsp; ziautomate.netlify.app &nbsp;·&nbsp; @ziautomate.sl</p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:16px 40px;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:11px;color:#9ca3af;text-align:center;">
              ziautomate S.L. &nbsp;·&nbsp; Madrid, España<br>
              Si no deseas recibir más emails, responde con <em>No gracias</em>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""
