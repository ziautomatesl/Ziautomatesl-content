import os
import io
import requests
from PIL import Image, ImageFilter

W, H = 1080, 1920

KEYWORDS = {
    'email':       'email marketing laptop professional',
    'whatsapp':    'smartphone messaging mobile professional',
    'cita':        'appointment calendar planner office',
    'reserva':     'booking reservation hotel restaurant',
    'factura':     'invoice accounting business paperwork',
    'lead':        'business meeting handshake client',
    'red':         'social media content creator phone',
    'instagram':   'social media influencer content phone',
    'tiktok':      'social media video creator phone',
    'crm':         'crm software database business',
    'tienda':      'ecommerce online shopping laptop',
    'almacen':     'warehouse storage logistics',
    'restaurant':  'restaurant kitchen chef food',
    'clinic':      'medical clinic health professional',
    'inmobiliar':  'real estate house property',
    'n8n':         'automation workflow technology',
    'make':        'automation software workflow',
    'ia':          'artificial intelligence technology',
    'robot':       'robot technology future',
    'propuesta':   'business proposal presentation meeting',
    'negocio':     'business entrepreneur office professional',
    'cliente':     'customer service business meeting',
    'seguimiento': 'business follow up communication',
    'automatiz':   'automation technology business workflow',
}


def _keywords(topic):
    t = topic.lower()
    for key, kw in KEYWORDS.items():
        if key in t:
            return kw
    return 'business technology office modern'


def _cover_crop(img, tw, th):
    """Resize + center crop to fill tw×th exactly."""
    src_ratio = img.width / img.height
    tgt_ratio = tw / th
    if src_ratio > tgt_ratio:
        scale = th / img.height
    else:
        scale = tw / img.width
    nw = max(tw, int(img.width  * scale))
    nh = max(th, int(img.height * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top  = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def fetch_background_videos(topic, n=3):
    """Download n portrait video clips from Pexels. Returns list of local file paths."""
    api_key = os.environ.get('PEXELS_API_KEY', '')
    if not api_key:
        print("PEXELS_API_KEY not set, sin vídeo de fondo")
        return []

    kw = _keywords(topic)
    headers = {'Authorization': api_key}
    url = (f'https://api.pexels.com/videos/search'
           f'?query={requests.utils.quote(kw)}&orientation=portrait&per_page={n}&size=medium')

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        videos = resp.json().get('videos', [])
        paths = []
        for i, video in enumerate(videos):
            files = video.get('video_files', [])

            def _score(f):
                q  = f.get('quality', '')
                fh = f.get('height', 0)
                fw = f.get('width', 1)
                portrait = 100 if fh > fw else 0
                quality  = {'hd': 50, 'sd': 20}.get(q, 5)
                size_ok  = 10 if fh <= 1920 else 0
                return portrait + quality + size_ok

            best = sorted(files, key=_score, reverse=True)
            if not best:
                continue
            link = best[0].get('link')
            if not link:
                continue

            path = f'/tmp/zia_bgvid_{i}.mp4'
            r = requests.get(link, timeout=60, stream=True)
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            paths.append(path)
            print(f"  Vídeo {i+1}: {best[0].get('quality')} "
                  f"{best[0].get('width')}x{best[0].get('height')}")

        print(f"Descargados {len(paths)} vídeos de Pexels para '{topic}'")
        return paths
    except Exception as e:
        print(f"Pexels video error: {e}")
        return []


def fetch_backgrounds(topic, n=3):
    """Download n portrait photos from Pexels related to topic. Returns list of PIL RGB images."""
    api_key = os.environ.get('PEXELS_API_KEY', '')
    if not api_key:
        print("PEXELS_API_KEY not set, using fallback background")
        return []

    kw = _keywords(topic)
    headers = {'Authorization': api_key}
    url = (f'https://api.pexels.com/v1/search'
           f'?query={requests.utils.quote(kw)}&orientation=portrait&per_page={n}&size=large')

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        photos = resp.json().get('photos', [])
        images = []
        for photo in photos:
            src = photo.get('src', {})
            img_url = src.get('large2x') or src.get('large') or src.get('medium')
            if not img_url:
                continue
            ir = requests.get(img_url, timeout=30)
            img = Image.open(io.BytesIO(ir.content)).convert('RGB')
            img = _cover_crop(img, W, H)
            images.append(img)
        print(f"Descargadas {len(images)} imágenes de Pexels para '{topic}'")
        return images
    except Exception as e:
        print(f"Pexels error: {e}")
        return []
