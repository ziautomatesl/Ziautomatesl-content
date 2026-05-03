import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip, VideoFileClip, concatenate_videoclips
from get_backgrounds import fetch_background_videos
from robot_behavior import build_timeline, get_behavior

W, H  = 1080, 1920
FPS   = 30
BG    = (5,   5,  14)
CYAN  = (0, 220, 255)
WHITE = (255, 255, 255)
GREY  = (105, 120, 142)


# ── Fuentes ───────────────────────────────────────────────────────────────────
def _load_font(p, s):
    try:    return ImageFont.truetype(p, s)
    except: return ImageFont.load_default()

def _get_fonts():
    b = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    r = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(b):
        b = "C:/Windows/Fonts/arialbd.ttf"
        r = "C:/Windows/Fonts/arial.ttf"
    return {"brand": _load_font(b,86), "sub": _load_font(r,44),
            "cap":   _load_font(b,56), "tag": _load_font(r,34)}


# ── Timing helpers ────────────────────────────────────────────────────────────
def _glow(t, wt):
    for w in wt:
        if w["start"]-0.05 <= t <= w["end"]+0.12:
            return 1.0
    return 0.15

def _word_at(t, wt):
    for w in wt:
        if w["start"]-0.03 <= t <= w["end"]+0.08:
            return w["word"]
    return None

def _last_words(t, wt, n=8):
    spoken = [w for w in wt if w["start"] <= t+0.08]
    return spoken[-n:] if spoken else []


# ── Background helpers ────────────────────────────────────────────────────────
def _make_overlay():
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    for y in range(H):
        if y < 135:
            a = 210
        elif y < 400:
            a = int(80 - (y-135)*0.22)
        elif y < 1400:
            a = int(28 + (y-400)*0.02)
        elif y < 1700:
            a = int(52 + (y-1400)*0.30)
        else:
            a = min(210, int(142 + (y-1700)*0.23))
        d.line([(0,y),(W,y)], fill=(0,3,10,a))
    return ov

def _solid_bg():
    bg = Image.new("RGB",(W,H),BG)
    d  = ImageDraw.Draw(bg)
    for x in range(0,W+58,58):
        for y in range(0,H+58,58):
            d.ellipse([(x-1,y-1),(x+1,y+1)],fill=(0,22,42))
    return bg


def _prepare_bg_video(video_paths, target_duration):
    """Load, resize/crop and loop video clips to cover target_duration."""
    clips = []
    for p in video_paths:
        try:
            c = VideoFileClip(p).without_audio()
            src_ratio = c.w / c.h
            tgt_ratio = W / H
            if src_ratio > tgt_ratio:
                c = c.resized(height=H)
            else:
                c = c.resized(width=W)
            x1 = max(0, (c.w - W) // 2)
            y1 = max(0, (c.h - H) // 2)
            c = c.cropped(x1=x1, y1=y1, width=W, height=H)
            clips.append(c)
        except Exception as e:
            print(f"Error cargando vídeo {p}: {e}")

    if not clips:
        return None

    total = sum(c.duration for c in clips)
    if total < target_duration:
        loops = int(target_duration / total) + 2
        clips = clips * loops

    combined = concatenate_videoclips(clips)
    return combined.subclipped(0, target_duration)


# ── Vignette ──────────────────────────────────────────────────────────────────
_VIGNETTE = None
def _get_vignette():
    global _VIGNETTE
    if _VIGNETTE is None:
        v  = Image.new("RGBA",(W,H),(0,0,0,0))
        dv = ImageDraw.Draw(v)
        cx2, cy2 = W//2, H//2
        for r in range(max(W,H)//2, 0, -4):
            dist = r / (max(W,H)//2)
            a = int(max(0, (dist-0.55)*1.8*180))
            dv.ellipse([(cx2-r,cy2-r),(cx2+r,cy2+r)], outline=(0,0,0,a), width=4)
        _VIGNETTE = v
    return _VIGNETTE


# ── Subtitle ──────────────────────────────────────────────────────────────────
def _subtitle(draw, t, wt, fonts):
    words = _last_words(t, wt)
    if not words: return
    cur  = _word_at(t, wt)
    sy   = H - 210
    full = " ".join(w["word"] for w in words)
    bb   = draw.textbbox((W//2, sy), full, font=fonts["cap"], anchor="mm")
    pad  = 22
    draw.rounded_rectangle([(bb[0]-pad,bb[1]-12),(bb[2]+pad,bb[3]+12)],
                            radius=14, fill=(0,0,0,215))
    draw.rounded_rectangle([(bb[0]-pad,bb[1]-12),(bb[2]+pad,bb[3]+12)],
                            radius=14, outline=(0,86,140), width=2)
    xc = bb[0]+pad
    for wd in words:
        col = CYAN if wd["word"]==cur else WHITE
        wb  = draw.textbbox((xc,sy), wd["word"], font=fonts["cap"], anchor="lm")
        draw.text((xc,sy), wd["word"], fill=col, font=fonts["cap"], anchor="lm")
        xc  = wb[2] + draw.textbbox((0,0)," ",font=fonts["cap"])[2]


# ── MAIN ──────────────────────────────────────────────────────────────────────
def create_animated_video(audio_path, word_timings, output_path="zia_video.mp4",
                          topic="", script_text=""):
    fonts    = _get_fonts()
    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    print(f"Descargando vídeos Pexels para '{topic}'...")
    video_paths = fetch_background_videos(topic, n=3)

    print("Preparando vídeo de fondo...")
    bg_clip  = _prepare_bg_video(video_paths, duration)
    fallback = _solid_bg()
    overlay  = _make_overlay()
    vignette = _get_vignette()

    def make_frame(t):
        # 1. Background frame
        if bg_clip is not None:
            frame = Image.fromarray(bg_clip.get_frame(t).astype('uint8'))
        else:
            frame = fallback.copy()

        frame = frame.convert("RGBA")
        frame.paste(overlay, (0,0), overlay)
        frame = frame.convert("RGB")
        draw  = ImageDraw.Draw(frame)

        # 2. Vignette
        frame.paste(vignette, (0,0), vignette)
        draw = ImageDraw.Draw(frame)

        # 3. Subtitle
        _subtitle(draw, t, word_timings, fonts)

        # 4. Header
        draw.rectangle([(0,0),(W,130)], fill=(0,4,14,235))
        draw.rectangle([(0,127),(W,131)], fill=CYAN)
        draw.text((W//2,65), "ziautomate", fill=CYAN,
                  font=fonts["brand"], anchor="mm")

        # 5. Topic badge
        if topic:
            tl = topic.upper()[:36]
            ty = 202
            tb = draw.textbbox((W//2,ty), tl, font=fonts["tag"], anchor="mm")
            draw.rounded_rectangle(
                [(tb[0]-20,tb[1]-10),(tb[2]+20,tb[3]+10)],
                radius=20, fill=(0,0,0,155), outline=(0,86,140), width=1)
            draw.text((W//2,ty), tl, fill=CYAN, font=fonts["tag"], anchor="mm")

        # 6. Footer
        draw.rectangle([(0,H-114),(W,H)], fill=(0,4,14,235))
        draw.rectangle([(0,H-117),(W,H-113)], fill=CYAN)
        draw.text((W//2,H-68), "ziautomate.netlify.app",
                  fill=CYAN, font=fonts["sub"], anchor="mm")
        draw.text((W//2,H-26), "automatización · IA · pymes",
                  fill=GREY, font=fonts["tag"], anchor="mm")

        return np.array(frame)

    video = VideoClip(make_frame, duration=duration)
    video = video.with_audio(audio)
    video.write_videofile(output_path, fps=FPS, codec="libx264",
                          audio_codec="aac", preset="faster", logger=None)

    for p in video_paths:
        try: os.remove(p)
        except: pass

    return output_path


def upload_for_instagram(video_path):
    import requests
    with open(video_path,"rb") as f:
        r = requests.post("https://0x0.st",files={"file":f},timeout=120)
    return r.text.strip()
