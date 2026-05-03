import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
import requests

ROBOT_PATH = os.path.join(os.path.dirname(__file__), "robot.png")
W, H = 1080, 1920
FPS = 30
BG = (8, 8, 20)
CYAN = (0, 220, 255)
WHITE = (255, 255, 255)
GREY = (120, 130, 150)


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def _get_fonts():
    # Linux (GitHub Actions)
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    # Windows fallback
    if not os.path.exists(bold):
        bold = "C:/Windows/Fonts/arialbd.ttf"
        regular = "C:/Windows/Fonts/arial.ttf"
    return {
        "brand": _load_font(bold, 88),
        "sub_brand": _load_font(regular, 52),
        "caption": _load_font(bold, 58),
    }


def _glow_intensity(t, word_timings):
    for w in word_timings:
        if w["start"] - 0.05 <= t <= w["end"] + 0.12:
            return 1.0
    return 0.15


def _current_subtitle(t, word_timings, max_words=6):
    spoken = [w for w in word_timings if w["start"] <= t + 0.1]
    if not spoken:
        return ""
    return " ".join(w["word"] for w in spoken[-max_words:])


def _precompute_glow_levels(robot, levels=12):
    arr = np.array(robot).astype(float)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    cyan_mask = (r < 80) & (g > 140) & (b > 180)
    rendered = []
    for i in range(levels + 1):
        intensity = i / levels
        out = arr.copy()
        out[..., 0] = np.clip(r + cyan_mask * intensity * 90, 0, 255)
        out[..., 1] = np.clip(g + cyan_mask * intensity * 110, 0, 255)
        out[..., 2] = np.clip(b + cyan_mask * intensity * 70, 0, 255)
        rendered.append(Image.fromarray(out.astype(np.uint8), "RGBA"))
    return rendered


def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4"):
    # Cargar y escalar robot
    robot = Image.open(ROBOT_PATH).convert("RGBA")
    rw = 880
    rh = int(robot.height * rw / robot.width)
    robot = robot.resize((rw, rh), Image.LANCZOS)
    rx = (W - rw) // 2
    ry = int(H * 0.24)

    # Pre-calcular niveles de brillo (evita procesar píxeles cada frame)
    glow_levels = 12
    robot_frames = _precompute_glow_levels(robot, glow_levels)

    # Fondo estático
    bg = Image.new("RGB", (W, H), BG)

    fonts = _get_fonts()
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    def make_frame(t):
        frame = bg.copy()
        draw = ImageDraw.Draw(frame)

        # Logo superior
        draw.text((W // 2, 110), "ziautomate", fill=CYAN, font=fonts["brand"], anchor="mm")

        # Línea decorativa
        draw.line([(W // 2 - 250, 175), (W // 2 + 250, 175)], fill=CYAN, width=3)

        # Robot con brillo según si habla o no
        intensity = _glow_intensity(t, word_timings)
        idx = round(intensity * glow_levels)
        frame.paste(robot_frames[idx], (rx, ry), robot_frames[idx])

        # Subtítulo en la parte inferior
        subtitle = _current_subtitle(t, word_timings)
        if subtitle:
            sy = H - 260
            # Sombra para legibilidad
            draw.text((W // 2 + 2, sy + 2), subtitle, fill=(0, 0, 0), font=fonts["caption"], anchor="mm")
            draw.text((W // 2, sy), subtitle, fill=WHITE, font=fonts["caption"], anchor="mm")

        # Web en la parte más inferior
        draw.text((W // 2, H - 100), "ziautomate.netlify.app", fill=CYAN, font=fonts["sub_brand"], anchor="mm")

        return np.array(frame)

    video = VideoClip(make_frame, duration=duration)
    video = video.set_audio(audio)
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
    """Sube el video a hosting temporal para que Instagram pueda descargarlo."""
    print("Subiendo video para Instagram...")
    with open(video_path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    url = r.text.strip()
    print(f"URL: {url}")
    return url
