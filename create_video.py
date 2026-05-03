import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from generate_robot import robot_frame, RW, RH
from get_backgrounds import fetch_backgrounds

W, H   = 1080, 1920
FPS    = 30
BG     = (6,   6,  16)
CYAN   = (0, 220, 255)
WHITE  = (255, 255, 255)
GREY   = (110, 125, 148)


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


# ── Gradient overlay: image visible top, darker bottom ───────────────────────
def _make_overlay():
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(H):
        if y < 135:
            a = 195
        elif y < 450:
            a = int(25 + (y-135) * 0.06)
        elif y < 780:
            a = int(44 + (y-450) * 0.14)
        else:
            a = min(195, int(90 + (y-780) * 0.10))
        d.line([(0, y), (W, y)], fill=(0, 3, 10, a))
    return ov


# ── Fallback sólido ───────────────────────────────────────────────────────────
def _solid_bg():
    bg = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(bg)
    for x in range(0, W+58, 58):
        for y in range(0, H+58, 58):
            draw.ellipse([(x-1, y-1), (x+1, y+1)], fill=(0, 26, 46))
    return bg


# ── Background crossfade ──────────────────────────────────────────────────────
def _bg_frame(t, duration, images, fallback):
    if not images:
        return fallback.copy().convert("RGBA")
    n = len(images)
    seg = duration / n
    i = min(int(t / seg), n - 1)
    st = t - i * seg
    fade = 0.55
    if st < fade and i > 0:
        return Image.blend(images[i-1].convert("RGBA"),
                           images[i].convert("RGBA"), st / fade)
    if st > seg - fade and i < n - 1:
        return Image.blend(images[i].convert("RGBA"),
                           images[i+1].convert("RGBA"),
                           (st - (seg - fade)) / fade)
    return images[i].convert("RGBA")


# ── Subtítulo ─────────────────────────────────────────────────────────────────
def _subtitle(draw, t, wt, fonts):
    words = _last_words(t, wt)
    if not words:
        return
    current = _word_at(t, wt)
    sy = H - 215
    full = " ".join(w["word"] for w in words)
    bb = draw.textbbox((W//2, sy), full, font=fonts["cap"], anchor="mm")
    pad = 22
    draw.rounded_rectangle([(bb[0]-pad, bb[1]-12), (bb[2]+pad, bb[3]+12)],
                            radius=14, fill=(0, 0, 0, 215))
    draw.rounded_rectangle([(bb[0]-pad, bb[1]-12), (bb[2]+pad, bb[3]+12)],
                            radius=14, outline=(0, 90, 145), width=2)
    xc = bb[0] + pad
    for wd in words:
        col = CYAN if wd["word"] == current else WHITE
        wb = draw.textbbox((xc, sy), wd["word"], font=fonts["cap"], anchor="lm")
        draw.text((xc, sy), wd["word"], fill=col, font=fonts["cap"], anchor="lm")
        xc = wb[2] + draw.textbbox((0, 0), " ", font=fonts["cap"])[2]


# ── MAIN ──────────────────────────────────────────────────────────────────────
def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    fonts    = _get_fonts()
    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    print(f"Descargando fondos Pexels para '{topic}'...")
    bg_imgs  = fetch_backgrounds(topic, n=3)
    fallback = _solid_bg()
    overlay  = _make_overlay()

    # Robot position: centered, bottom above footer
    rx = (W - RW) // 2
    ry = H - RH - 115

    def make_frame(t):
        # 1. Background image (Pexels or fallback)
        frame = _bg_frame(t, duration, bg_imgs, fallback)

        # 2. Gradient overlay
        frame.paste(overlay, (0, 0), overlay)
        frame = frame.convert("RGB")
        draw = ImageDraw.Draw(frame)

        # 3. Glow halo behind robot when speaking
        glow_v = _glow(t, word_timings)
        if glow_v > 0.5:
            hr = int(260 + 18 * math.sin(t * 13))
            hcx, hcy = W // 2, ry + RH // 2
            draw.ellipse([(hcx-hr, hcy-hr), (hcx+hr, hcy+hr)],
                         outline=(0, int(50*glow_v), int(90*glow_v)), width=3)

        # 4. Robot frame
        bob    = int(8 * math.sin(t * math.pi * 1.55))
        mouth  = abs(math.sin(t * math.pi * 7.5)) * (1.0 if glow_v > 0.5 else 0.0)
        blink  = _blink(t)
        # Pass blink as glow reduction on eyes
        effective_glow = glow_v * (1 - blink * 0.85)

        r_img = robot_frame(mouth_open=mouth, glow=effective_glow, bob=bob)
        frame.paste(r_img, (rx, ry), r_img)

        draw = ImageDraw.Draw(frame)

        # 5. Header bar
        draw.rectangle([(0, 0), (W, 130)], fill=(0, 5, 16, 230))
        draw.rectangle([(0, 127), (W, 131)], fill=CYAN)
        draw.text((W//2, 65), "ziautomate", fill=CYAN, font=fonts["brand"], anchor="mm")

        # 6. Topic badge
        if topic:
            tl = topic.upper()[:36]
            ty = 205
            tb = draw.textbbox((W//2, ty), tl, font=fonts["tag"], anchor="mm")
            draw.rounded_rectangle(
                [(tb[0]-20, tb[1]-10), (tb[2]+20, tb[3]+10)],
                radius=20, fill=(0, 0, 0, 155), outline=(0, 90, 145), width=1)
            draw.text((W//2, ty), tl, fill=CYAN, font=fonts["tag"], anchor="mm")

        # 7. Subtitle
        _subtitle(draw, t, word_timings, fonts)

        # 8. Footer bar
        draw.rectangle([(0, H-118), (W, H)], fill=(0, 5, 16, 230))
        draw.rectangle([(0, H-121), (W, H-117)], fill=CYAN)
        draw.text((W//2, H-72), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub"], anchor="mm")
        draw.text((W//2, H-30), "automatización · IA · pymes",
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
