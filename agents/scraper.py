import os
import json
import re
import time
import requests
from agents.config import GOOGLE_PLACES_API_KEY, CAMPAIGN_CITY, CAMPAIGN_SECTOR

LEADS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "leads.json")


def load_leads() -> list:
    try:
        with open(LEADS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_leads(leads: list):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def known_emails(leads: list) -> set:
    return {l["email"].lower().strip() for l in leads if l.get("email")}

def known_names(leads: list) -> set:
    return {l.get("negocio", "").lower().strip() for l in leads}

def _already_exists(leads: list, name: str, email: str) -> bool:
    if email and email.lower().strip() in known_emails(leads):
        return True
    return name.lower().strip() in known_names(leads)


def _is_valid_email(email: str) -> bool:
    email = email.lower()
    # Nombres de archivo que el regex confunde con emails (logo@2x.png, foto.jpg...)
    bad_endings = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
                   ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".mp4", ".pdf")
    if email.endswith(bad_endings):
        return False
    # Imágenes retina tipo logo@2x / icon@3x
    local, _, domain = email.partition("@")
    if re.fullmatch(r"\d+x[\w.\-]*", domain.split(".")[0]):
        return False
    # Restos de URL codificada (%20nombre@...) u otros caracteres raros
    if "%" in local or not local:
        return False
    blocked = {"example", "sentry", "schema", "test", "noreply", "no-reply",
               "w3.org", "domain.com", "email.com", "yoursite", "wixpress",
               "placeholder", "your-email", "user@"}
    return not any(b in email for b in blocked)


def _extract_email(url: str) -> str:
    if not url:
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ziautomate-bot/1.0)"}
        resp = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
        from urllib.parse import unquote
        text = unquote(resp.text)  # %20nombre@... → nombre@...
        emails = re.findall(r'[a-zA-Z0-9._+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
        for email in emails:
            if _is_valid_email(email):
                return email.lower()
    except Exception:
        pass
    return ""


def _place_details(place_id: str) -> dict:
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": place_id, "fields": "website,formatted_phone_number",
                    "language": "es", "key": GOOGLE_PLACES_API_KEY},
            timeout=8,
        )
        return resp.json().get("result", {})
    except Exception:
        return {}


def _search_places(sector: str, city: str, max_results: int) -> list:
    if not GOOGLE_PLACES_API_KEY:
        print("  ⚠ GOOGLE_PLACES_API_KEY no configurada — usando datos de demo")
        return [
            {"name": f"{sector.capitalize()} Demo {i}", "address": f"Calle Mayor {i*10}, {city}",
             "rating": round(3.8 + i*0.1, 1), "website": "", "phone": f"+34 91{i:07d}"}
            for i in range(1, min(6, max_results + 1))
        ]

    results, page_token = [], None
    while len(results) < max_results:
        params = {"query": f"{sector} en {city}", "language": "es", "region": "es",
                  "key": GOOGLE_PLACES_API_KEY}
        if page_token:
            params["pagetoken"] = page_token
            time.sleep(2)
        try:
            data = requests.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params=params, timeout=10
            ).json()
        except Exception as e:
            print(f"  Error Places API: {e}")
            break

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"  Places API status: {data.get('status')}")
            break

        for place in data.get("results", []):
            det = _place_details(place["place_id"])
            results.append({
                "name":    place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "rating":  place.get("rating", 0),
                "website": det.get("website", ""),
                "phone":   det.get("formatted_phone_number", ""),
            })

        page_token = data.get("next_page_token")
        if not page_token or len(results) >= max_results:
            break

    return results[:max_results]


def scrape_leads(city: str = None, sector: str = None, max_new: int = 20) -> list:
    city   = city   or CAMPAIGN_CITY
    sector = sector or CAMPAIGN_SECTOR

    existing = load_leads()
    print(f"  Leads existentes en base de datos: {len(existing)}")

    places = _search_places(sector, city, max_results=max_new * 2)
    print(f"  Negocios encontrados en Google Maps: {len(places)}")

    new_leads  = []
    seen_emails = known_emails(existing)
    seen_names  = known_names(existing)

    for place in places:
        if len(new_leads) >= max_new:
            break

        name_key = place["name"].lower().strip()
        if name_key in seen_names:
            print(f"    Saltando (nombre ya existe): {place['name']}")
            continue

        print(f"    Procesando: {place['name']}...")
        email = _extract_email(place["website"])

        if email and email.lower().strip() in seen_emails:
            print(f"    Saltando (email ya existe): {email}")
            continue

        lead = {
            "id":       int(time.time() * 1000) + len(new_leads),
            "negocio":  place["name"],
            "sector":   sector.capitalize(),
            "ciudad":   city,
            "email":    email,
            "telefono": place["phone"],
            "web":      place["website"],
            "rating":   place["rating"],
            "notas":    f"⭐ {place['rating']} · Google Maps",
            "estado":   "pendiente",
            "fecha":    "",
        }
        new_leads.append(lead)
        if email:
            seen_emails.add(email.lower().strip())
        seen_names.add(name_key)
        time.sleep(0.5)

    all_leads = new_leads + existing
    save_leads(all_leads)
    print(f"  Leads nuevos añadidos: {len(new_leads)}")
    return new_leads
