import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from generate_robot import create_robot

W, H = 1080, 1920
FPS = 30
BG      = (8, 8, 20)
CYAN    = (0, 220, 255)
DCYAN   = (0, 90, 130)
WHITE   = (255, 255, 255)
GREY    = (120, 130, 150)


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def _get_fonts():
    bold    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(bold):
        bold    = "C:/Windows/Fonts/arialbd.ttf"
        regular = "C:/Windows/Fonts/arial.ttf"
    return {
        "brand":     _load_font(bold,    90),
        "sub_brand": _load_font(regular, 46),
        "caption":   _load_font(bold,    56),
        "tag":       _load_font(regular, 36),
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
        out[..., 0] = np.clip(r + cyan_mask * intensity * 90,  0, 255)
        out[..., 1] = np.clip(g + cyan_mask * intensity * 110, 0, 255)
        out[..., 2] = np.clip(b + cyan_mask * intensity * 70,  0, 255)
        rendered.append(Image.fromarray(out.astype(np.uint8), "RGBA"))
    return rendered


def _draw_background(w, h):
    """Fondo oscuro con rejilla de puntos cyan tenue."""
    bg = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(bg)
    step = 60
    for x in range(0, w, step):
        for y in range(0, h, step):
            draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=(0, 35, 55))
    return bg


def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4"):
    robot = create_robot(800, 900)
    rw = 800
    rh = 900
    rx = (W - rw) // 2
    ry = int(H * 0.22)

    glow_levels = 12
    robot_frames = _precompute_glow_levels(robot, glow_levels)

    bg = _draw_background(W, H)
    fonts = _get_fonts()
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    def make_frame(t):
        frame = bg.copy()
        draw = ImageDraw.Draw(frame)

        # ── Franja superior ──────────────────────────────────────────
        draw.rectangle([(0, 0), (W, 155)], fill=(0, 10, 22))

        # Logo "ziautomate"
        draw.text((W // 2, 78), "ziautomate",
                  fill=CYAN, font=fonts["brand"], anchor="mm")

        # Línea inferior franja
        draw.rectangle([(0, 152), (W, 156)], fill=CYAN)

        # ── Robot ────────────────────────────────────────────────────
        intensity = _glow_intensity(t, word_timings)
        idx = round(intensity * glow_levels)
        frame.paste(robot_frames[idx], (rx, ry), robot_frames[idx])

        # ── Subtítulo ────────────────────────────────────────────────
        subtitle = _current_subtitle(t, word_timings)
        if subtitle:
            sy = H - 240
            # Caja translúcida detrás del texto
            bbox = draw.textbbox((W // 2, sy), subtitle,
                                 font=fonts["caption"], anchor="mm")
            pad = 18
            draw.rounded_rectangle(
                [(bbox[0]-pad, bbox[1]-pad), (bbox[2]+pad, bbox[3]+pad)],
                radius=12, fill=(0, 0, 0, 180)
            )
            draw.text((W // 2 + 2, sy + 2), subtitle,
                      fill=(0, 0, 0), font=fonts["caption"], anchor="mm")
            draw.text((W // 2, sy), subtitle,
                      fill=WHITE, font=fonts["caption"], anchor="mm")

        # ── Franja inferior ──────────────────────────────────────────
        draw.rectangle([(0, H - 130), (W, H)], fill=(0, 10, 22))
        draw.rectangle([(0, H - 133), (W, H - 129)], fill=CYAN)
        draw.text((W // 2, H - 65), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub_brand"], anchor="mm")
        draw.text((W // 2, H - 28), "automatización · IA · pymes",
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
    """Sube el video a hosting temporal para que Instagram pueda descargarlo."""
    import requests
    print("Subiendo video para Instagram...")
    with open(video_path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    url = r.text.strip()
    print(f"URL: {url}")
    return url
