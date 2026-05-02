import requests
import time
import os

INSTAGRAM_API = "https://graph.instagram.com/v21.0"

def post_reel(video_url, caption):
    account_id = os.environ["INSTAGRAM_ACCOUNT_ID"]
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    # Paso 1: crear contenedor del video
    print("Creando contenedor en Instagram...")
    container = requests.post(
        f"{INSTAGRAM_API}/{account_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": True,
            "access_token": token,
        }
    ).json()

    if "error" in container:
        raise Exception(f"Error creando contenedor: {container['error']['message']}")

    container_id = container["id"]
    print(f"Contenedor creado: {container_id}")

    # Paso 2: esperar a que Instagram procese el video (máx 3 min)
    print("Esperando que Instagram procese el video...")
    for _ in range(18):
        time.sleep(10)
        status = requests.get(
            f"{INSTAGRAM_API}/{container_id}",
            params={"fields": "status_code", "access_token": token}
        ).json()

        code = status.get("status_code", "")
        print(f"Estado: {code}")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise Exception("Instagram rechazó el video")

    # Paso 3: publicar
    print("Publicando Reel...")
    result = requests.post(
        f"{INSTAGRAM_API}/{account_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        }
    ).json()

    if "error" in result:
        raise Exception(f"Error publicando: {result['error']['message']}")

    print(f"Reel publicado! ID: {result.get('id')}")
    return result
