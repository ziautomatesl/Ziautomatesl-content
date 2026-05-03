import math
import random
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from generate_robot import draw_robot
from visual_scenes import build_scene

W, H   = 1080, 1920
FPS    = 30
BG     = (8,   8,  20)
CYAN   = (0, 220, 255)
DCYAN  = (0,  70, 110)
WHITE  = (255, 255, 255)
GREY   = (110, 125, 148)
BLACK  = (0,   0,   0)


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
        "brand":  _load_font(bold,    88),
        "sub":    _load_font(regular, 44),
        "cap":    _load_font(bold,    56),
        "tag":    _load_font(regular, 34),
        "word":   _load_font(bold,    60),
    }


# ── Partículas de fondo ───────────────────────────────────────────────────────
def _make_particles(n=55, seed=42):
    rng = random.Random(seed)
    return [
        {
            "x":     rng.uniform(0, W),
            "y":     rng.uniform(0, H),
            "speed": rng.uniform(18, 60),
            "r":     rng.uniform(1.2, 3.5),
            "alpha": rng.uniform(0.15, 0.55),
        }
        for _ in range(n)
    ]


# ── Timings de palabras ───────────────────────────────────────────────────────
def _word_at(t, word_timings):
    for w in word_timings:
        if w["start"] - 0.03 <= t <= w["end"] + 0.08:
            return w["word"]
    return None


def _last_words(t, word_timings, n=7):
    spoken = [w for w in word_timings if w["start"] <= t + 0.08]
    return spoken[-n:] if spoken else []


def _glow(t, word_timings):
    for w in word_timings:
        if w["start"] - 0.05 <= t <= w["end"] + 0.12:
            return 1.0
    return 0.15


# ── Blink schedule ────────────────────────────────────────────────────────────
def _blink(t):
    """Devuelve 0-1 para el parpadeo (1 = cerrado)."""
    # Parpadeos cada ~3s, duración 0.1s
    blink_times = [2.1, 5.3, 8.7, 12.0, 15.4, 18.9, 22.3, 26.0, 29.5, 33.0, 36.8]
    for bt in blink_times:
        dt = t - bt
        if 0 <= dt < 0.12:
            return math.sin(dt / 0.12 * math.pi)
    return 0.0


# ── Fondo con rejilla de puntos ───────────────────────────────────────────────
def _static_bg():
    bg = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(bg)
    step = 58
    for x in range(0, W + step, step):
        for y in range(0, H + step, step):
            draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=(0, 28, 48))
    return bg


# ── Render de partículas ──────────────────────────────────────────────────────
def _render_particles(draw, particles, t):
    for p in particles:
        y = (p["y"] - p["speed"] * t) % H
        c = (0, int(180 * p["alpha"]), int(255 * p["alpha"]))
        r = p["r"]
        draw.ellipse([(p["x"]-r, y-r), (p["x"]+r, y+r)], fill=c)


# ── Barras de voz ─────────────────────────────────────────────────────────────
def _render_voice_bars(draw, t, word_timings, cx, y, n=9):
    speaking = _glow(t, word_timings) > 0.5
    for i in range(n):
        phase = i * 0.7 + t * 12
        h = int(8 + 28 * abs(math.sin(phase))) if speaking else 4
        x = cx - (n // 2) * 16 + i * 16
        alpha_c = CYAN if speaking else (0, 60, 90)
        draw.rectangle([(x-4, y - h), (x+4, y + h)], fill=alpha_c)


# ── Subtítulo con palabra actual resaltada ────────────────────────────────────
def _render_subtitle(draw, t, word_timings, fonts):
    words = _last_words(t, word_timings)
    if not words:
        return
    current = _word_at(t, word_timings)
    text = " ".join(w["word"] for w in words)

    sy = H - 230
    bbox = draw.textbbox((W // 2, sy), text, font=fonts["cap"], anchor="mm")
    pad = 20
    draw.rounded_rectangle(
        [(bbox[0]-pad, bbox[1]-pad*0.7), (bbox[2]+pad, bbox[3]+pad*0.7)],
        radius=14, fill=(0, 0, 0, 200)
    )

    # Palabra a palabra: la activa en cyan, las demás en blanco
    x_cursor = bbox[0] + pad

    for wdata in words:
        color = CYAN if wdata["word"] == current else WHITE
        wb = draw.textbbox((x_cursor, sy), wdata["word"], font=fonts["cap"], anchor="lm")
        draw.text((x_cursor, sy), wdata["word"], fill=color,
                  font=fonts["cap"], anchor="lm")
        x_cursor = wb[2] + draw.textbbox((0, 0), " ", font=fonts["cap"])[2]


# ── Barra de progreso ─────────────────────────────────────────────────────────
def _render_progress(draw, t, duration):
    bar_y = H - 138
    draw.rectangle([(60, bar_y), (W-60, bar_y+4)], fill=(0, 40, 65))
    filled = int((W - 120) * min(1, t / duration))
    if filled > 0:
        draw.rectangle([(60, bar_y), (60 + filled, bar_y+4)], fill=CYAN)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    particles  = _make_particles(55)
    bg_static  = _static_bg()
    fonts      = _get_fonts()
    audio      = AudioFileClip(audio_path)
    duration   = audio.duration

    cx_robot = W // 2
    cy_robot = int(H * 0.56)

    # Escena informativa pre-renderizada (se pega cada frame, no se recalcula)
    scene_img = build_scene(topic, script_text, fonts, W, H)

    def make_frame(t):
        frame = bg_static.copy()
        draw  = ImageDraw.Draw(frame)

        # Partículas flotando
        _render_particles(draw, particles, t)

        # Panel informativo (tema + dato + flujo)
        frame.paste(scene_img, (0, 0), scene_img)

        # Scan-line horizontal descendente (cada 4 segundos)
        scan_t = t % 4.0
        scan_y = int(scan_t / 4.0 * H)
        draw.rectangle([(0, scan_y), (W, scan_y+2)], fill=(0, 50, 80))

        # Halo pulsante alrededor del robot cuando habla
        glow_v = _glow(t, word_timings)
        if glow_v > 0.5:
            halo_r = int(350 + 18 * math.sin(t * 14))
            draw.ellipse(
                [(cx_robot-halo_r, cy_robot-halo_r),
                 (cx_robot+halo_r, cy_robot+halo_r)],
                outline=(0, int(60*glow_v), int(100*glow_v)),
                width=3
            )

        # ── Robot animado ────────────────────────────────────────────
        bob_y    = int(7 * math.sin(t * math.pi * 1.6))
        speaking = glow_v > 0.5
        mouth_v  = abs(math.sin(t * math.pi * 8)) * (1.0 if speaking else 0.0)
        blink_v  = _blink(t)

        robot_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_robot(robot_img, cx_robot, cy_robot + bob_y,
                   mouth=mouth_v, blink=blink_v, glow=glow_v)
        frame.paste(robot_img, (0, 0), robot_img)

        # ── Franja superior ──────────────────────────────────────────
        draw.rectangle([(0, 0), (W, 152)], fill=(0, 8, 20))
        draw.rectangle([(0, 149), (W, 153)], fill=CYAN)
        draw.text((W//2, 76), "ziautomate",
                  fill=CYAN, font=fonts["brand"], anchor="mm")

        # ── Barras de voz bajo la marca ──────────────────────────────
        _render_voice_bars(draw, t, word_timings, W//2, 135)

        # ── Subtítulo con palabra resaltada ──────────────────────────
        _render_subtitle(draw, t, word_timings, fonts)

        # ── Franja inferior ──────────────────────────────────────────
        draw.rectangle([(0, H-128), (W, H)], fill=(0, 8, 20))
        draw.rectangle([(0, H-131), (W, H-127)], fill=CYAN)

        _render_progress(draw, t, duration)

        draw.text((W//2, H-80), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub"], anchor="mm")
        draw.text((W//2, H-36), "automatización · IA · pymes",
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
