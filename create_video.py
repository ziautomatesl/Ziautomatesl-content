import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from animate_robot import load_robot, make_frame as robot_frame
from get_backgrounds import fetch_backgrounds

W, H   = 1080, 1920
FPS    = 30
BG     = (6,   6,  16)
CYAN   = (0, 220, 255)
WHITE  = (255, 255, 255)
GREY   = (110, 125, 148)

ROBOT_PATH = os.path.join(os.path.dirname(__file__), "robot.png")


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


# ── Overlay gradient ──────────────────────────────────────────────────────────
def _make_overlay():
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d  = ImageDraw.Draw(ov)
    for y in range(H):
        if y < 135:
            a = 190
        elif y < 420:
            a = int(18 + (y-135) * 0.055)
        elif y < 750:
            a = int(33 + (y-420) * 0.10)
        else:
            a = min(160, int(66 + (y-750) * 0.08))
        d.line([(0, y), (W, y)], fill=(0, 3, 10, a))
    return ov


def _solid_bg():
    bg   = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(bg)
    for x in range(0, W+58, 58):
        for y in range(0, H+58, 58):
            draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=(0, 24, 44))
    return bg


# ── Background crossfade ──────────────────────────────────────────────────────
def _bg_frame(t, duration, images, fallback):
    if not images:
        return fallback.copy().convert("RGBA")
    n   = len(images)
    seg = duration / n
    i   = min(int(t / seg), n - 1)
    st  = t - i * seg
    fade = 0.6
    if st < fade and i > 0:
        return Image.blend(images[i-1].convert("RGBA"),
                           images[i].convert("RGBA"), st / fade)
    if st > seg - fade and i < n - 1:
        return Image.blend(images[i].convert("RGBA"),
                           images[i+1].convert("RGBA"),
                           (st - (seg - fade)) / fade)
    return images[i].convert("RGBA")


# ── Partículas de energía cyan ────────────────────────────────────────────────
def _particles(draw, t, robot_cx, robot_top, glow, n=14):
    if glow < 0.5:
        return
    import random
    rand = random.Random(int(t * 8))
    for _ in range(n):
        age  = rand.random()
        px   = robot_cx + rand.randint(-180, 180)
        py   = robot_top + rand.randint(0, 300) - int(age * 180 * glow)
        pr   = int(2 + rand.random() * 4 * glow)
        draw.ellipse([(px-pr, py-pr), (px+pr, py+pr)],
                     fill=(0, int(180*glow), int(255*glow)))


# ── Subtítulo ─────────────────────────────────────────────────────────────────
def _subtitle(draw, t, wt, fonts):
    words = _last_words(t, wt)
    if not words:
        return
    current = _word_at(t, wt)
    sy  = H - 215
    full = " ".join(w["word"] for w in words)
    bb  = draw.textbbox((W//2, sy), full, font=fonts["cap"], anchor="mm")
    pad = 22
    draw.rounded_rectangle([(bb[0]-pad, bb[1]-12), (bb[2]+pad, bb[3]+12)],
                            radius=14, fill=(0, 0, 0, 215))
    draw.rounded_rectangle([(bb[0]-pad, bb[1]-12), (bb[2]+pad, bb[3]+12)],
                            radius=14, outline=(0, 88, 142), width=2)
    xc = bb[0] + pad
    for wd in words:
        col = CYAN if wd["word"] == current else WHITE
        wb  = draw.textbbox((xc, sy), wd["word"], font=fonts["cap"], anchor="lm")
        draw.text((xc, sy), wd["word"], fill=col, font=fonts["cap"], anchor="lm")
        xc  = wb[2] + draw.textbbox((0, 0), " ", font=fonts["cap"])[2]


# ── MAIN ──────────────────────────────────────────────────────────────────────
def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    fonts    = _get_fonts()
    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    print(f"Cargando robot y fondos...")
    robot_base, robot_meta = load_robot(ROBOT_PATH)
    rw, rh = robot_meta['w'], robot_meta['h']

    # Position: centered horizontally, bottom above footer
    rx = (W - rw) // 2
    ry = H - rh - 108

    print(f"Descargando fondos Pexels para '{topic}'...")
    bg_imgs  = fetch_backgrounds(topic, n=3)
    fallback = _solid_bg()
    overlay  = _make_overlay()

    robot_cx = W // 2
    robot_top = ry

    def make_frame(t):
        # 1. Background
        frame = _bg_frame(t, duration, bg_imgs, fallback)
        frame.paste(overlay, (0, 0), overlay)
        frame = frame.convert("RGB")
        draw  = ImageDraw.Draw(frame)

        glow_v   = _glow(t, word_timings)
        blink_v  = _blink(t)
        eff_glow = glow_v * (1.0 - blink_v * 0.9)

        # 2. Energy particles when speaking
        _particles(draw, t, robot_cx, robot_top + 60, glow_v)

        # 3. Halo
        if glow_v > 0.5:
            hr = int(240 + 20 * math.sin(t * 13))
            hcy = ry + rh // 2
            draw.ellipse([(robot_cx-hr, hcy-hr), (robot_cx+hr, hcy+hr)],
                         outline=(0, int(44*glow_v), int(80*glow_v)), width=3)

        # 4. Animated robot (2.5D parallax layers)
        mouth_v  = abs(math.sin(t * math.pi * 7.5)) * (1.0 if glow_v > 0.5 else 0.0)
        r_img = robot_frame(robot_base, robot_meta, t, mouth_v, eff_glow)
        frame.paste(r_img, (rx, ry), r_img)

        draw = ImageDraw.Draw(frame)

        # 5. Header
        draw.rectangle([(0, 0), (W, 130)], fill=(0, 5, 15, 235))
        draw.rectangle([(0, 127), (W, 131)], fill=CYAN)
        draw.text((W//2, 65), "ziautomate", fill=CYAN, font=fonts["brand"], anchor="mm")

        # 6. Topic badge
        if topic:
            tl = topic.upper()[:36]
            ty = 205
            tb = draw.textbbox((W//2, ty), tl, font=fonts["tag"], anchor="mm")
            draw.rounded_rectangle(
                [(tb[0]-20, tb[1]-10), (tb[2]+20, tb[3]+10)],
                radius=20, fill=(0, 0, 0, 155), outline=(0, 88, 142), width=1)
            draw.text((W//2, ty), tl, fill=CYAN, font=fonts["tag"], anchor="mm")

        # 7. Subtitle
        _subtitle(draw, t, word_timings, fonts)

        # 8. Footer
        draw.rectangle([(0, H-116), (W, H)], fill=(0, 5, 15, 235))
        draw.rectangle([(0, H-119), (W, H-115)], fill=CYAN)
        draw.text((W//2, H-70), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub"], anchor="mm")
        draw.text((W//2, H-28), "automatización · IA · pymes",
                  fill=GREY, font=fonts["tag"], anchor="mm")

        return np.array(frame)

    video = VideoClip(make_frame, duration=duration)
    video = video.with_audio(audio)
    video.write_videofile(output_path, fps=FPS, codec="libx264",
                          audio_codec="aac", preset="faster", logger=None)
    return output_path


def upload_for_instagram(video_path):
    import requests
    with open(video_path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f}, timeout=120)
    return r.text.strip()
