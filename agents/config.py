import os

# ── Parámetros de campaña ────────────────────────────────────
DAILY_LIMIT     = int(os.getenv("DAILY_LIMIT", "10"))

# Ciudades que rotan semanalmente
CITY_ROTATION = [
    "Madrid", "Barcelona", "Valencia", "Sevilla",
    "Bilbao", "Málaga", "Zaragoza", "Murcia",
]

# Sectores que rotan por día de la semana
SECTOR_ROTATION = [
    "peluquería",    # martes
    "restaurante",   # miércoles
    "clínica",       # jueves
    "taller",        # viernes
    "academia",      # (semana siguiente empieza aquí)
    "inmobiliaria",
    "gimnasio",
    "farmacia",
]

def get_daily_city() -> str:
    if os.getenv("CAMPAIGN_CITY"):
        return os.getenv("CAMPAIGN_CITY")
    from datetime import date
    week = date.today().isocalendar()[1]
    return CITY_ROTATION[week % len(CITY_ROTATION)]

def get_daily_sector() -> str:
    if os.getenv("CAMPAIGN_SECTOR"):
        return os.getenv("CAMPAIGN_SECTOR")
    from datetime import date
    idx = date.today().weekday() - 1  # mar=0, mié=1, jue=2, vie=3
    return SECTOR_ROTATION[max(0, idx) % len(SECTOR_ROTATION)]

CAMPAIGN_CITY   = get_daily_city()
CAMPAIGN_SECTOR = get_daily_sector()

# ── APIs ─────────────────────────────────────────────────────
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY", "")

# ── Gmail SMTP ───────────────────────────────────────────────
SMTP_HOST    = "smtp.gmail.com"
SMTP_PORT    = 587
SMTP_USER    = os.getenv("SENDER_EMAIL", "ziautomate.sl@gmail.com")
SMTP_PASS    = os.getenv("GMAIL_APP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "ziautomate.sl@gmail.com")
SENDER_NAME  = "ziautomate"

# ── Templates por sector ─────────────────────────────────────
SECTOR_TEMPLATES = {
    "peluquería": {
        "pain":       "no-shows y citas canceladas sin avisar",
        "solution":   "recordatorios automáticos por WhatsApp + lista de espera automática",
        "case_study": "Una peluquería en Valencia tenía un 30% de no-shows los fines de semana. Con recordatorios automáticos y lista de espera bajaron al 5% en el primer mes — sin contratar a nadie.",
        "stat":       "el 30% de tus citas se pueden estar perdiendo sin que lo sepas",
    },
    "restaurante": {
        "pain":       "reservas que no aparecen y pocas reseñas en Google",
        "solution":   "confirmación automática de reservas + solicitud de reseña post-visita",
        "case_study": "Un restaurante en Barcelona tenía el 30% de mesas vacías los sábados por no-shows. Con confirmación automática pasaron de 4.1 a 4.7 estrellas en 2 meses.",
        "stat":       "las mesas vacías de fin de semana cuestan dinero real",
    },
    "clínica": {
        "pain":       "cancelaciones de última hora y huecos sin rellenar",
        "solution":   "recordatorios 72h + 24h + mismo día, con lista de espera automática",
        "case_study": "Una psicóloga en Madrid perdía 640€ al mes por cancelaciones tardías. Con recordatorios automatizados redujo las pérdidas un 70%.",
        "stat":       "cada cita cancelada sin rellenar vale entre 60€ y 120€",
    },
    "taller": {
        "pain":       "clientes que llaman sin sistema de citas y seguimiento manual",
        "solution":   "WhatsApp automático para citas + seguimiento post-servicio",
        "case_study": "Un taller en Sevilla duplicó sus citas mensuales solo con un sistema de respuesta automática en menos de 5 minutos.",
        "stat":       "el 78% de las ventas va al negocio que contesta primero",
    },
    "academia": {
        "pain":       "alumnos que se dan de baja sin avisar y pagos manuales",
        "solution":   "recordatorios de retención automáticos + cobros automatizados",
        "case_study": "Una academia de idiomas redujo las bajas un 25% en 2 meses con mensajes automáticos a alumnos que llevaban 10 días sin entrar.",
        "stat":       "recuperar un alumno cuesta 5x menos que captar uno nuevo",
    },
    "inmobiliaria": {
        "pain":       "consultas a cualquier hora sin respuesta y leads sin seguimiento",
        "solution":   "respuesta automática 24/7 + seguimiento de leads automatizado",
        "case_study": "Una inmobiliaria en Málaga recuperó 4 operaciones al mes que perdía por no responder fuera de horario. La IA responde al instante y agenda visitas.",
        "stat":       "el cliente que no recibe respuesta en 5 minutos ya habló con tu competencia",
    },
    "default": {
        "pain":       "tareas repetitivas que consumen tiempo sin generar valor",
        "solution":   "automatización de procesos y respuesta automática a clientes",
        "case_study": "Una pyme típica recupera entre 15 y 25 horas al mes con 3 automatizaciones básicas.",
        "stat":       "el 80% de las tareas repetitivas de tu negocio se pueden automatizar",
    },
}

def get_template(sector: str) -> dict:
    sector_lower = sector.lower()
    for key in SECTOR_TEMPLATES:
        if key in sector_lower:
            return SECTOR_TEMPLATES[key]
    return SECTOR_TEMPLATES["default"]
