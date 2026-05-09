import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def post_youtube(video_path: str, title: str, description: str, tags: list = None):
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    )
    creds.refresh(Request())

    youtube = build("youtube", "v3", credentials=creds)

    # Tags deduplicated, each max 30 chars, total max 500 chars
    clean_tags = []
    total = 0
    for t in (tags or []):
        t = t[:30]
        if total + len(t) + 1 <= 500:
            clean_tags.append(t)
            total += len(t) + 1

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": clean_tags,
            "categoryId": "28",  # Science & Technology
            "defaultLanguage": "es",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    print("Subiendo video a YouTube...")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Subiendo... {int(status.progress() * 100)}%")

    print(f"Video publicado en YouTube! ID: {response['id']}")
    return response["id"]
