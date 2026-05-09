"""
Orquestador de campaña outreach B2B — ziautomate
Flujo: scrape Google Maps → genera email con Gemini → envía por Brevo → actualiza leads.json
"""
import time
from datetime import date
from agents.scraper         import scrape_leads, load_leads, save_leads, known_emails
from agents.email_generator import generate_email
from agents.email_sender    import send_email
from agents.config          import DAILY_LIMIT, CAMPAIGN_CITY, CAMPAIGN_SECTOR


def run():
    print(f"\n{'='*55}")
    print(f"  ZIA Campaign Bot · {date.today()}")
    print(f"  Ciudad: {CAMPAIGN_CITY}  |  Sector: {CAMPAIGN_SECTOR}")
    print(f"  Límite diario: {DAILY_LIMIT} emails")
    print(f"{'='*55}\n")

    # ── PASO 1: Buscar nuevos negocios ───────────────────────
    print("PASO 1: Buscando nuevos negocios en Google Maps...")
    scrape_leads(city=CAMPAIGN_CITY, sector=CAMPAIGN_SECTOR, max_new=DAILY_LIMIT * 3)

    # ── PASO 2: Filtrar pendientes con email ─────────────────
    leads    = load_leads()
    enviados_emails = {
        l["email"].lower().strip()
        for l in leads
        if l.get("estado") in ("enviado", "interesado", "reunion", "cerrado") and l.get("email")
    }

    pendientes = []
    for l in leads:
        if l.get("estado") != "pendiente":
            continue
        email = l.get("email", "").lower().strip()
        if not email:
            continue
        if email in enviados_emails:
            # Marcar como enviado si por algún motivo quedó pendiente
            l["estado"] = "enviado"
            print(f"  Corregido estado duplicado: {l['negocio']} ({email})")
            continue
        pendientes.append(l)

    print(f"\nPASO 2: Leads pendientes con email: {len(pendientes)}")

    if not pendientes:
        print("No hay leads pendientes con email. Fin.")
        save_leads(leads)
        return

    # ── PASO 3: Generar y enviar emails ──────────────────────
    print(f"\nPASO 3: Enviando hasta {DAILY_LIMIT} emails...")
    enviados = 0

    for lead in pendientes[:DAILY_LIMIT]:
        email = lead["email"].lower().strip()

        # Guardia final: nunca enviar dos veces al mismo email
        if email in enviados_emails:
            print(f"  Saltando (ya enviado en esta sesión): {email}")
            continue

        print(f"\n  → {lead['negocio']} ({email})")

        email_data = generate_email(lead)
        success    = send_email(
            email,
            email_data["subject"],
            email_data["body"],
            email_data.get("html", ""),
        )

        if success:
            lead["estado"] = "enviado"
            lead["fecha"]  = date.today().strftime("%d/%m/%y")
            asunto_corto   = email_data["subject"][:50]
            lead["notas"]  = (lead.get("notas", "") + f" | {asunto_corto}").strip(" |")
            enviados_emails.add(email)
            enviados += 1

        time.sleep(4)

    # ── PASO 4: Guardar estado actualizado ───────────────────
    save_leads(leads)

    print(f"\n{'='*55}")
    print(f"  Emails enviados hoy: {enviados}/{DAILY_LIMIT}")
    print(f"  Total leads en BD:   {len(leads)}")
    print(f"  Emails ya enviados:  {len(enviados_emails)}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run()
