import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, AudioFileClip
from generate_robot import robot_frame, RW, RH
from get_backgrounds import fetch_backgrounds

W, H  = 1080, 1920
FPS   = 30
BG    = (5,   5,  14)
CYAN  = (0, 220, 255)
WHITE = (255, 255, 255)
GREY  = (105, 120, 142)

ROBOT_X = (W - RW) // 2
ROBOT_Y = H - RH - 105   # robot stands just above footer


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


# ── Gesture selection from spoken words ──────────────────────────────────────
_GESTURE_MAP = [
    (['euro','€','dinero','cobro','factura','precio','pago','sueldo',
      'gana','inver'], 'thumbsup'),
    (['tú','tu','negocio','empresa','pyme','autónom','tienda',
      'restau','clíni','inmobi'], 'point_cam'),
    (['automático','auto','solo','sistema','bot','ia','robot',
      'inteligenci','n8n','make'], 'explain'),
    (['hola','gracias','semana','mes','día','tiempo','hora',
      'minuto','segunda'], 'wave'),
    (['qué','cómo','por qué','problema','antes'], 'shrug'),
]

def _pick_gesture(recent_words: list[str]) -> str:
    text = " ".join(recent_words).lower()
    for keywords, gesture in _GESTURE_MAP:
        for kw in keywords:
            if kw in text:
                return gesture
    return 'neutral'


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

def _blink(t):
    for bt in [2.1,5.3,8.7,12.0,15.4,18.9,22.3,26.0,29.5,33.0,36.5]:
        dt = t - bt
        if 0 <= dt < 0.13:
            return math.sin(dt/0.13 * math.pi)
    return 0.0


# ── Background helpers ────────────────────────────────────────────────────────
def _make_overlay():
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    for y in range(H):
        if y < 135:           a = 195
        elif y < 400:         a = int(16 + (y-135)*0.05)
        elif y < 720:         a = int(29 + (y-400)*0.09)
        else:                 a = min(165, int(58 + (y-720)*0.09))
        d.line([(0,y),(W,y)], fill=(0,3,10,a))
    return ov

def _solid_bg():
    bg = Image.new("RGB",(W,H),BG)
    d  = ImageDraw.Draw(bg)
    for x in range(0,W+58,58):
        for y in range(0,H+58,58):
            d.ellipse([(x-1,y-1),(x+1,y+1)],fill=(0,22,42))
    return bg

def _bg_frame(t, dur, imgs, fb):
    if not imgs: return fb.copy().convert("RGBA")
    n=len(imgs); seg=dur/n; i=min(int(t/seg),n-1); st=t-i*seg; fade=0.6
    if st<fade and i>0:
        return Image.blend(imgs[i-1].convert("RGBA"),imgs[i].convert("RGBA"),st/fade)
    if st>seg-fade and i<n-1:
        return Image.blend(imgs[i].convert("RGBA"),imgs[i+1].convert("RGBA"),
                           (st-(seg-fade))/fade)
    return imgs[i].convert("RGBA")


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


# ── Energy particles ──────────────────────────────────────────────────────────
def _particles(draw, t, glow):
    if glow < 0.5: return
    import random
    rand = random.Random(int(t*9))
    for _ in range(16):
        age  = rand.random()
        px   = W//2 + rand.randint(-200,200)
        py   = ROBOT_Y + rand.randint(0,320) - int(age*210*glow)
        pr   = int(1.5 + rand.random()*4*glow)
        br   = int(160*glow); bg2 = int(248*glow)
        draw.ellipse([(px-pr,py-pr),(px+pr,py+pr)], fill=(0,br,bg2))


# ── Vignette post-processing ──────────────────────────────────────────────────
_VIGNETTE = None
def _get_vignette():
    global _VIGNETTE
    if _VIGNETTE is None:
        v = Image.new("RGBA",(W,H),(0,0,0,0))
        dv = ImageDraw.Draw(v)
        cx2,cy2 = W//2, H//2
        for r in range(max(W,H)//2, 0, -4):
            dist = r / (max(W,H)//2)
            a = int(max(0, (dist-0.55)*1.8*180))
            dv.ellipse([(cx2-r,cy2-r),(cx2+r,cy2+r)], outline=(0,0,0,a), width=4)
        _VIGNETTE = v
    return _VIGNETTE


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
    vignette = _get_vignette()

    # Gesture change interval: switch pose every ~7 seconds
    def _gesture(t, wt):
        recent = _last_words(t, wt, n=12)
        words  = [w["word"] for w in recent]
        return _pick_gesture(words)

    def make_frame(t):
        # 1. Background
        frame = _bg_frame(t, duration, bg_imgs, fallback)
        frame.paste(overlay, (0,0), overlay)
        frame = frame.convert("RGB")
        draw  = ImageDraw.Draw(frame)

        glow_v  = _glow(t, word_timings)
        blink_v = _blink(t)
        eff_g   = glow_v * (1.0 - blink_v*0.88)

        # 2. Particles
        _particles(draw, t, glow_v)

        # 3. Halo
        if glow_v > 0.5:
            hr  = int(230 + 22*math.sin(t*12))
            hcy = ROBOT_Y + RH//2
            draw.ellipse([(W//2-hr, hcy-hr),(W//2+hr, hcy+hr)],
                         outline=(0,int(42*glow_v),int(76*glow_v)), width=3)

        # 4. Robot with gesture + lip sync
        bob     = int(9 * math.sin(t*math.pi*1.5))
        mouth_v = abs(math.sin(t*math.pi*7)) * (1.0 if glow_v>0.5 else 0.0)
        gesture = _gesture(t, word_timings)

        r_img = robot_frame(t, mouth_v, eff_g, pose=gesture, bob=bob)
        frame.paste(r_img, (ROBOT_X, ROBOT_Y), r_img)

        draw = ImageDraw.Draw(frame)

        # 5. Vignette
        frame.paste(vignette, (0,0), vignette)
        draw = ImageDraw.Draw(frame)

        # 6. Header
        draw.rectangle([(0,0),(W,130)], fill=(0,4,14,235))
        draw.rectangle([(0,127),(W,131)], fill=CYAN)
        draw.text((W//2,65), "ziautomate", fill=CYAN,
                  font=fonts["brand"], anchor="mm")

        # 7. Topic badge
        if topic:
            tl = topic.upper()[:36]
            ty = 202
            tb = draw.textbbox((W//2,ty), tl, font=fonts["tag"], anchor="mm")
            draw.rounded_rectangle(
                [(tb[0]-20,tb[1]-10),(tb[2]+20,tb[3]+10)],
                radius=20, fill=(0,0,0,155), outline=(0,86,140),width=1)
            draw.text((W//2,ty), tl, fill=CYAN, font=fonts["tag"], anchor="mm")

        # 8. Subtitle
        _subtitle(draw, t, word_timings, fonts)

        # 9. Footer
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
    return output_path


def upload_for_instagram(video_path):
    import requests
    with open(video_path,"rb") as f:
        r = requests.post("https://0x0.st",files={"file":f},timeout=120)
    return r.text.strip()
