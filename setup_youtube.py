"""
Ejecuta este script UNA VEZ para renovar el refresh token de YouTube.
Abre el navegador automáticamente, autorizas con Google, y guarda
el token directamente en el secret de GitHub.

    python setup_youtube.py

Necesitas: YOUTUBE_CLIENT_ID y YOUTUBE_CLIENT_SECRET
(Google Cloud Console → APIs & Services → Credentials → tu app OAuth)
"""
import sys
import subprocess
import base64
import json
import getpass

# ── instalar deps si faltan ────────────────────────────────────────────────────
for pkg in ("google-auth-oauthlib", "pynacl", "requests"):
    try:
        __import__(pkg.replace("-", "_").split(".")[0])
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

import os
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from nacl import encoding, public as nacl_public

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or input("GitHub Personal Access Token (repo/secrets): ").strip()
REPO         = "Ziautomatesl/Ziautomatesl-content"
SCOPES       = ["https://www.googleapis.com/auth/youtube.upload"]


def _update_secret(name: str, value: str):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=headers)
    r.raise_for_status()
    key_data = r.json()

    pub_key = nacl_public.PublicKey(key_data["key"].encode(), encoding.Base64Encoder())
    box = nacl_public.SealedBox(pub_key)
    encrypted = base64.b64encode(box.encrypt(value.encode())).decode()

    r = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{name}",
        headers=headers,
        json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
    )
    r.raise_for_status()


def main():
    print("=== Renovar token YouTube ===\n")
    print("Encuéntralos en: console.cloud.google.com")
    print("  APIs & Services → Credentials → tu app OAuth 2.0\n")

    client_id     = input("YOUTUBE_CLIENT_ID:     ").strip()
    client_secret = input("YOUTUBE_CLIENT_SECRET: ").strip()

    config = {
        "installed": {
            "client_id":     client_id,
            "client_secret": client_secret,
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    print("\nAbriendo navegador para autorizar con Google...")
    flow  = InstalledAppFlow.from_client_config(config, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    refresh_token = creds.refresh_token
    if not refresh_token:
        print("ERROR: Google no devolvió refresh token. Asegúrate de revocar el acceso previo en:")
        print("  myaccount.google.com/permissions  →  elimina 'ziautomate' → vuelve a correr el script")
        sys.exit(1)

    print("\nActualizando secret YOUTUBE_REFRESH_TOKEN en GitHub...")
    _update_secret("YOUTUBE_REFRESH_TOKEN", refresh_token)

    print("\n✅ Listo. YouTube vuelve a funcionar en el próximo run automático.")


if __name__ == "__main__":
    main()
