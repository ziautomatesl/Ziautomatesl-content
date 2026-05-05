"""
Ejecuta este script UNA VEZ en tu ordenador para generar la sesión de Instagram.
Luego copia el valor generado como secreto INSTAGRAM_SESSION en GitHub.

    python setup_instagram.py
"""
import json
import base64
import getpass

def main():
    from instagrapi import Client

    print("=== Setup sesión Instagram ===\n")
    username = input("Usuario de Instagram: ").strip()
    password = getpass.getpass("Contraseña (no se muestra): ")

    cl = Client()
    cl.delay_range = [2, 5]

    try:
        cl.login(username, password)
    except Exception as e:
        # Instagram puede pedir código 2FA
        if "two_factor" in str(e).lower() or "challenge" in str(e).lower():
            code = input("Código 2FA / verificación de Instagram: ").strip()
            cl.two_factor_login(code)
        else:
            raise

    session = cl.get_settings()
    encoded = base64.b64encode(json.dumps(session).encode()).decode()

    print("\n✅ Sesión generada correctamente.")
    print("\n── Añade estos 3 secretos en GitHub Actions ──")
    print(f"  INSTAGRAM_USERNAME  →  {username}")
    print(f"  INSTAGRAM_PASSWORD  →  (tu contraseña)")
    print(f"  INSTAGRAM_SESSION   →  (valor de abajo, cópialo entero)\n")
    print(encoded)
    print("\nVe a: github.com/ziautomatesl/Ziautomatesl-content → Settings → Secrets → Actions")

if __name__ == "__main__":
    main()
