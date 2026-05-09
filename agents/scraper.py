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


def _already_exists(leads: list, name: str, ciudad: str) -> bool:
    name_lower  = name.lower().strip()
    city_lower  = ciudad.lower().strip()
    return any(
        l.get("negocio", "").lower().strip() == name_lower and
        l.get("ciudad",  "").lower().strip() == city_lower
        for l in leads
    )


def _extract_email(url: str) -> str:
    if not url:
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ziautomate-bot/1.0)"}
        resp = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
        emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', resp.text)
        blocked = {"example", "sentry", "schema", "test", "noreply", "no-reply",
                   "w3.org", "domain.com", "email.com", "yoursite"}
        for email in emails:
            if not any(b in email.lower() for b in blocked):
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

    new_leads = []
    for place in places:
        if len(new_leads) >= max_new:
            break
        if _already_exists(existing, place["name"], city):
            print(f"    Saltando (ya existe): {place['name']}")
            continue

        print(f"    Procesando: {place['name']}...")
        email = _extract_email(place["website"])

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
        time.sleep(0.5)

    all_leads = new_leads + existing
    save_leads(all_leads)
    print(f"  Leads nuevos añadidos: {len(new_leads)}")
    return new_leads
