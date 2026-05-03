import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from generate_robot import draw_robot
from get_backgrounds import fetch_backgrounds

W, H   = 1080, 1920
FPS    = 30
BG     = (8,   8,  20)
CYAN   = (0, 220, 255)
WHITE  = (255, 255, 255)
GREY   = (110, 125, 148)
BLACK  = (0,   0,   0)

POSES = ['neutral', 'point_right', 'raise_right', 'explain', 'point_left']


# ── Fuentes ───────────────────────────────────────────────────────────────────
def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _get_fonts():
    bold    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(bold):
        bold    = "C:/Windows/Fonts/arialbd.ttf"
        regular = "C:/Windows/Fonts/arial.ttf"
    return {
        "brand": _load_font(bold,    86),
        "sub":   _load_font(regular, 44),
        "cap":   _load_font(bold,    56),
        "tag":   _load_font(regular, 34),
    }


# ── Gradiente oscuro sobre la imagen ─────────────────────────────────────────
def _dark_gradient(w, h):
    """RGBA overlay: transparente arriba, opaco abajo (zona del robot)."""
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for y in range(h):
        if y < 140:
            alpha = 200          # barra marca
        elif y < 400:
            alpha = int(30 + (y - 140) * 0.10)   # imagen visible
        elif y < 700:
            alpha = int(45 + (y - 400) * 0.25)
        else:
            alpha = min(210, int(120 + (y - 700) * 0.13))  # zona robot
        draw.line([(0, y), (w, y)], fill=(0, 4, 12, alpha))
    return grad


# ── Fondo sólido de respaldo ──────────────────────────────────────────────────
def _solid_bg():
    bg = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(bg)
    step = 58
    for x in range(0, W + step, step):
        for y in range(0, H + step, step):
            draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=(0, 28, 48))
    return bg


# ── Timings ───────────────────────────────────────────────────────────────────
def _glow(t, wt):
    for w in wt:
        if w["start"] - 0.05 <= t <= w["end"] + 0.12:
            return 1.0
    return 0.15


def _word_at(t, wt):
    for w in wt:
        if w["start"] - 0.03 <= t <= w["end"] + 0.08:
            return w["word"]
    return None


def _last_words(t, wt, n=6):
    spoken = [w for w in wt if w["start"] <= t + 0.08]
    return spoken[-n:] if spoken else []


def _blink(t):
    for bt in [2.1, 5.3, 8.7, 12.0, 15.4, 18.9, 22.3, 26.0, 29.5, 33.0]:
        dt = t - bt
        if 0 <= dt < 0.12:
            return math.sin(dt / 0.12 * math.pi)
    return 0.0


def _pose(t):
    """Cambia de pose cada ~7 segundos."""
    return POSES[int(t / 7) % len(POSES)]


# ── Background con crossfade ──────────────────────────────────────────────────
def _get_bg_frame(t, duration, bg_images, fallback):
    if not bg_images:
        return fallback.copy().convert("RGBA")

    n = len(bg_images)
    seg = duration / n
    seg_t = t % seg
    seg_i = min(int(t / seg), n - 1)

    fade_dur = 0.6
    if seg_t < fade_dur and seg_i > 0:
        alpha = seg_t / fade_dur
        base = bg_images[seg_i - 1].convert("RGBA")
        over = bg_images[seg_i].convert("RGBA")
        return Image.blend(base, over, alpha)
    elif seg_t > seg - fade_dur and seg_i < n - 1:
        alpha = (seg_t - (seg - fade_dur)) / fade_dur
        base = bg_images[seg_i].convert("RGBA")
        over = bg_images[seg_i + 1].convert("RGBA")
        return Image.blend(base, over, alpha)
    else:
        return bg_images[seg_i].convert("RGBA")


# ── Subtítulo animado ─────────────────────────────────────────────────────────
def _render_subtitle(draw, t, wt, fonts):
    words = _last_words(t, wt)
    if not words:
        return
    current = _word_at(t, wt)
    sy = H - 220

    # Caja de fondo
    text_full = " ".join(w["word"] for w in words)
    bbox = draw.textbbox((W // 2, sy), text_full, font=fonts["cap"], anchor="mm")
    pad = 22
    draw.rounded_rectangle(
        [(bbox[0]-pad, bbox[1]-12), (bbox[2]+pad, bbox[3]+12)],
        radius=14, fill=(0, 0, 0, 210)
    )
    # Borde cyan
    draw.rounded_rectangle(
        [(bbox[0]-pad, bbox[1]-12), (bbox[2]+pad, bbox[3]+12)],
        radius=14, outline=(0, 100, 160), width=2
    )

    # Palabras: activa en cyan, resto en blanco
    x_cur = bbox[0] + pad
    for wdata in words:
        color = CYAN if wdata["word"] == current else WHITE
        wb = draw.textbbox((x_cur, sy), wdata["word"], font=fonts["cap"], anchor="lm")
        draw.text((x_cur, sy), wdata["word"], fill=color, font=fonts["cap"], anchor="lm")
        x_cur = wb[2] + draw.textbbox((0, 0), " ", font=fonts["cap"])[2]


# ── MAIN ──────────────────────────────────────────────────────────────────────
def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    fonts    = _get_fonts()
    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    print(f"Descargando fondos de Pexels para '{topic}'...")
    bg_images = fetch_backgrounds(topic, n=3)
    fallback  = _solid_bg()
    gradient  = _dark_gradient(W, H)

    cx_robot = W // 2
    cy_robot = int(H * 0.73)   # robot en mitad inferior

    def make_frame(t):
        # 1. Fondo (Pexels o sólido)
        bg = _get_bg_frame(t, duration, bg_images, fallback)

        # 2. Gradiente oscuro encima
        bg.paste(gradient, (0, 0), gradient)

        frame = bg.convert("RGB")
        draw  = ImageDraw.Draw(frame)

        # 3. Halo pulsante
        glow_v = _glow(t, word_timings)
        if glow_v > 0.5:
            halo_r = int(300 + 20 * math.sin(t * 14))
            draw.ellipse(
                [(cx_robot - halo_r, cy_robot - halo_r),
                 (cx_robot + halo_r, cy_robot + halo_r)],
                outline=(0, int(55 * glow_v), int(95 * glow_v)),
                width=3
            )

        # 4. Robot animado con pose
        bob_y   = int(7 * math.sin(t * math.pi * 1.6))
        speaking = glow_v > 0.5
        mouth_v = abs(math.sin(t * math.pi * 8)) * (1.0 if speaking else 0.0)
        blink_v = _blink(t)
        pose_v  = _pose(t)

        robot_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_robot(robot_img, cx_robot, cy_robot + bob_y,
                   mouth=mouth_v, blink=blink_v, glow=glow_v, pose=pose_v)
        frame.paste(robot_img, (0, 0), robot_img)

        draw = ImageDraw.Draw(frame)   # redibujar sobre el robot

        # 5. Barra superior
        draw.rectangle([(0, 0), (W, 130)], fill=(0, 6, 18, 230))
        draw.rectangle([(0, 127), (W, 131)], fill=CYAN)
        draw.text((W // 2, 65), "ziautomate",
                  fill=CYAN, font=fonts["brand"], anchor="mm")

        # 6. Tema del video (zona visible sobre la foto)
        if topic:
            topic_short = topic.upper()[:38]
            ty = 220
            tbbox = draw.textbbox((W//2, ty), topic_short, font=fonts["tag"], anchor="mm")
            draw.rounded_rectangle(
                [(tbbox[0]-18, tbbox[1]-10), (tbbox[2]+18, tbbox[3]+10)],
                radius=20, fill=(0, 0, 0, 160), outline=(0, 100, 160), width=1
            )
            draw.text((W//2, ty), topic_short, fill=CYAN, font=fonts["tag"], anchor="mm")

        # 7. Subtítulo
        _render_subtitle(draw, t, word_timings, fonts)

        # 8. Barra inferior
        draw.rectangle([(0, H - 120), (W, H)], fill=(0, 6, 18, 230))
        draw.rectangle([(0, H - 123), (W, H - 119)], fill=CYAN)
        draw.text((W // 2, H - 72), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub"], anchor="mm")
        draw.text((W // 2, H - 30), "automatización · IA · pymes",
                  fill=GREY, font=fonts["tag"], anchor="mm")

        return np.array(frame)

    video = VideoClip(make_frame, duration=duration)
    video = video.with_audio(audio)
    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="faster",
        logger=None,
    )
    return output_path


def upload_for_instagram(video_path):
    import requests
    print("Subiendo video para Instagram...")
    with open(video_path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    url = r.text.strip()
    print(f"URL: {url}")
    return url
