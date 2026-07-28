"""
Genera la lista diaria de negocios a los que escribir por WhatsApp A MANO.

Solo incluye leads con MÓVIL (6xx/7xx) y SIN email — contactos que la campaña
de correo no puede tocar. No envía nada: produce whatsapp_hoy.md para copiar
y pegar desde el teléfono.

Uso:  python -m agents.whatsapp_list [cuantos]
"""
import io
import os
import re
import sys
from datetime import date

from agents.scraper import load_leads, save_leads

OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "whatsapp_hoy.md")

# Gancho por sector: la frase que explica qué le resuelves a ese negocio
GANCHOS = {
    "peluquería":   "los recordatorios de cita automáticos, para que no se caigan las reservas de última hora",
    "restaurante":  "la confirmación automática de reservas y pedir reseña después de cada visita",
    "clínica":      "los recordatorios de cita automáticos, para reducir las cancelaciones de última hora",
    "taller":       "responder al instante a quien pide cita, aunque estéis con las manos ocupadas",
    "academia":     "avisar solo a los alumnos que llevan días sin aparecer, antes de que se den de baja",
    "inmobiliaria": "responder a las consultas fuera de horario para no perder visitas",
    "gimnasio":     "recuperar a los socios que dejan de venir antes de que se den de baja",
    "farmacia":     "avisar a los clientes cuando su pedido está listo, sin llamar uno a uno",
}
GANCHO_DEFECTO = "automatizar las tareas repetitivas del día a día"

# El plural de "taller" no es "tallers"
PLURALES = {
    "peluquería": "peluquerías", "restaurante": "restaurantes",
    "clínica": "clínicas",       "taller": "talleres",
    "academia": "academias",     "inmobiliaria": "inmobiliarias",
    "gimnasio": "gimnasios",     "farmacia": "farmacias",
}


def _movil(lead: dict) -> bool:
    d = re.sub(r"\D", "", lead.get("telefono", ""))
    if d.startswith("34"):
        d = d[2:]
    return len(d) == 9 and d[0] in "67"


def _gancho(sector: str) -> str:
    s = sector.lower()
    for k, v in GANCHOS.items():
        if k in s:
            return v
    return GANCHO_DEFECTO


def mensaje(lead: dict) -> str:
    negocio = lead.get("negocio", "").split("|")[0].split("-")[0].strip()
    sector  = lead.get("sector", "negocio").lower()
    plural  = PLURALES.get(sector, sector + "s")
    return (
        f"Hola, ¿{negocio}? Soy Zia, de ziautomate. "
        f"Ayudo a {plural} de {lead.get('ciudad','')} con {_gancho(sector)}. "
        f"¿Te cuento en 2 minutos cómo funciona? Si no te encaja, sin problema."
    )


def observacion(lead: dict) -> str:
    notas = []
    rating = float(lead.get("rating") or 0)
    if rating >= 4.7:
        notas.append(f"{rating}★ muy bien valorado")
    elif rating >= 4.0:
        notas.append(f"{rating}★ correcto")
    elif rating > 0:
        notas.append(f"{rating}★ flojo — puede necesitar ayuda con reseñas")

    if not lead.get("web"):
        notas.append("sin web (poco digitalizado)")
    else:
        notas.append("tiene web")

    return " · ".join(notas)


def candidatos(limite: int = 15) -> list:
    leads = load_leads()
    pool = [
        l for l in leads
        if not l.get("email")
        and _movil(l)
        and l.get("estado") == "pendiente"
    ]
    # Primero los mejor valorados: más probable que el negocio funcione y pueda pagar
    pool.sort(key=lambda l: float(l.get("rating") or 0), reverse=True)

    # Un mismo local aparece a veces con dos nombres distintos y el mismo móvil
    vistos, unicos = set(), []
    for l in pool:
        tel = re.sub(r"\D", "", l.get("telefono", ""))
        if tel in vistos:
            continue
        vistos.add(tel)
        unicos.append(l)
    return unicos[:limite]


def generar(limite: int = 15) -> str:
    lista = candidatos(limite)
    hoy = date.today().strftime("%d/%m/%Y")

    lineas = [
        f"# WhatsApp a mano · {hoy}",
        "",
        f"{len(lista)} negocios con móvil y sin email. Escríbeles tú desde el teléfono.",
        "",
    ]

    for i, l in enumerate(lista, 1):
        tel = re.sub(r"\D", "", l["telefono"])
        if not tel.startswith("34"):
            tel = "34" + tel
        lineas += [
            f"## {i}. {l['negocio']}",
            f"- **Teléfono:** {l['telefono']}  ·  [Abrir chat](https://wa.me/{tel})",
            f"- **Dónde:** {l.get('ciudad','')} · {l.get('sector','')}",
            f"- **Observaciones:** {observacion(l)}",
            "",
            "**Mensaje:**",
            "```",
            mensaje(l),
            "```",
            "",
        ]

    texto = "\n".join(lineas)
    with io.open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    print(generar(n))
    print(f"\nGuardado en {OUT_FILE}")
