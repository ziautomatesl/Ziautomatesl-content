"""
Animated human avatar – "Sofía", professional AI presenter.
Pure Pillow drawing. Same interface as generate_robot.py (RW, RH, robot_frame).
"""
import math
from PIL import Image, ImageDraw

RW, RH = 960, 980

# ── Palette ───────────────────────────────────────────────────────────────────
SKIN      = (244, 196, 158)
SKIN_SH   = (208, 155, 112)
HAIR      = (35,  18,   8)
HAIR_HI   = (82,  50,  22)
EYE_W     = (248, 248, 252)
IRIS_C    = (52,  34,  18)
PUPIL_C   = (10,   6,   4)
BROW_C    = (42,  22,   8)
LIP_U     = (205,  90,  72)
LIP_L     = (185,  68,  52)
TEETH_C   = (248, 243, 238)
SHIRT     = (48, 104, 192)
SHIRT_SH  = (30,  72, 148)
COLLAR    = (242, 238, 230)

CX = RW // 2   # 480

# ── Layout ────────────────────────────────────────────────────────────────────
FACE_CY  = 310
FACE_RX  = 150
FACE_RY  = 185

EYE_LX, EYE_RX = CX - 60, CX + 60
EYE_Y           = FACE_CY - 32
ERW, ERH        = 44, 30

BROW_Y   = EYE_Y - 38
NOSE_CY  = FACE_CY + 40
MOUTH_CX = CX
MOUTH_CY = FACE_CY + 92
MRW, MRH = 52, 14

NECK_TOP = FACE_CY + FACE_RY - 22
NECK_W   = 58

_BLINKS = [2.3, 5.8, 9.2, 13.1, 17.4, 21.0, 25.5, 29.8, 34.2, 38.6]


def _blink(t):
    for bt in _BLINKS:
        dt = t - bt
        if 0 <= dt < 0.16:
            return math.sin(dt / 0.16 * math.pi)
    return 0.0


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _hair_back(draw):
    draw.polygon([
        (CX - 218, 760),
        (CX - 202, 175),
        (CX - 148,  72),
        (CX,         44),
        (CX + 148,   72),
        (CX + 202, 175),
        (CX + 218, 760),
    ], fill=HAIR)


def _body(draw):
    # Neck
    draw.rectangle(
        [CX - NECK_W, NECK_TOP, CX + NECK_W, NECK_TOP + 135],
        fill=SKIN_SH)
    sy = NECK_TOP + 100
    # Shirt
    draw.polygon([
        (CX - NECK_W - 18, sy),
        (CX + NECK_W + 18, sy),
        (CX + 530, RH + 80),
        (CX - 530, RH + 80),
    ], fill=SHIRT)
    # Shadow left side
    draw.polygon([
        (CX - NECK_W - 18, sy),
        (CX - 18, sy + 65),
        (CX - 530, RH + 80),
    ], fill=SHIRT_SH)
    # Collar V-neck
    draw.polygon([
        (CX - NECK_W - 14, sy),
        (CX + NECK_W + 14, sy),
        (CX + 30, sy + 90),
        (CX,      sy + 112),
        (CX - 30, sy + 90),
    ], fill=COLLAR)


def _ears(draw):
    for ex in (CX - FACE_RX + 4, CX + FACE_RX - 4):
        draw.ellipse([ex - 22, FACE_CY - 30,
                      ex + 22, FACE_CY + 30], fill=SKIN_SH)


def _face(draw):
    draw.ellipse([CX - FACE_RX - 5, FACE_CY - FACE_RY - 5,
                  CX + FACE_RX + 5, FACE_CY + FACE_RY + 5], fill=SKIN_SH)
    draw.ellipse([CX - FACE_RX, FACE_CY - FACE_RY,
                  CX + FACE_RX, FACE_CY + FACE_RY], fill=SKIN)
    # Soft cheek blush (brighter skin patch)
    for bx in (CX - 92, CX + 92):
        draw.ellipse([bx - 28, FACE_CY + 22, bx + 28, FACE_CY + 62],
                     fill=(238, 168, 138))


def _hair_front(draw):
    # Hairline overlapping top of face
    draw.polygon([
        (CX - 202, 175),
        (CX - 148,  72),
        (CX,         44),
        (CX + 148,   72),
        (CX + 202, 175),
        (CX + 142, 162),
        (CX,       138),
        (CX - 142, 162),
    ], fill=HAIR)
    # Highlight streak
    draw.line([(CX - 18, 60), (CX + 82, 135)], fill=HAIR_HI, width=8)


def _brows(draw, raised=False):
    dy = -8 if raised else 0
    for bx in (EYE_LX, EYE_RX):
        y = BROW_Y + dy
        draw.arc([bx - 40, y - 8, bx + 40, y + 22],
                 start=208, end=332, fill=BROW_C, width=10)


def _nose(draw):
    ny = NOSE_CY
    draw.ellipse([CX - 20, ny - 6, CX - 8,  ny + 11], fill=SKIN_SH)
    draw.ellipse([CX + 8,  ny - 6, CX + 20, ny + 11], fill=SKIN_SH)


def _eyes(draw, t, glow):
    bv   = _blink(t)
    ev   = min(255, int(190 + 65 * glow))   # iris brightness when speaking

    for ex in (EYE_LX, EYE_RX):
        ey  = EYE_Y
        erh = max(2, int(ERH * (1.0 - bv)))

        # Sclera
        draw.ellipse([ex - ERW, ey - erh, ex + ERW, ey + erh], fill=EYE_W)

        if bv > 0.85:
            draw.arc([ex - ERW, ey - 4, ex + ERW, ey + 4],
                     start=0, end=180, fill=BROW_C, width=3)
            continue

        # Iris
        ir = min(erh - 1, 26)
        draw.ellipse([ex - ir, ey - ir, ex + ir, ey + ir],
                     fill=(IRIS_C[0], min(255, IRIS_C[1] + int(ev * 0.08)),
                           min(255, IRIS_C[2] + int(ev * 0.10))))
        # Pupil
        pr = int(ir * 0.50)
        draw.ellipse([ex - pr, ey - pr, ex + pr, ey + pr], fill=PUPIL_C)
        # Highlight
        draw.ellipse([ex - pr + 4, ey - pr + 3,
                      ex - pr + 13, ey - pr + 11], fill=(255, 255, 255))
        # Upper eyelid line
        draw.arc([ex - ERW, ey - erh, ex + ERW, ey + erh],
                 start=208, end=332, fill=BROW_C, width=3)


def _mouth(draw, mouth_open):
    cx, cy = MOUTH_CX, MOUTH_CY

    if mouth_open < 0.08:
        # Closed smile
        draw.arc([cx - MRW, cy - MRW // 2,
                  cx + MRW, cy + MRW // 2],
                 start=12, end=168, fill=LIP_U, width=6)
        draw.ellipse([cx - MRW - 2, cy - 6, cx - MRW + 9, cy + 7], fill=LIP_U)
        draw.ellipse([cx + MRW - 9, cy - 6, cx + MRW + 2, cy + 7], fill=LIP_U)
    else:
        ow = int(MRW * 0.90)
        oh = max(7, int(mouth_open * MRW * 0.76))
        # Mouth interior
        draw.ellipse([cx - ow, cy - oh, cx + ow, cy + oh], fill=(32, 8, 5))
        # Teeth
        if mouth_open > 0.18:
            th = min(oh - 2, int(oh * 0.54))
            draw.ellipse([cx - ow + 9, cy - oh + 2,
                          cx + ow - 9, cy - oh + th + 4], fill=TEETH_C)
        # Upper lip
        draw.arc([cx - ow - 5, cy - oh - 12, cx + ow + 5, cy + 5],
                 start=200, end=340, fill=LIP_U, width=6)
        # Lower lip
        draw.arc([cx - ow - 4, cy - 6, cx + ow + 4, cy + oh + 11],
                 start=20, end=160, fill=LIP_L, width=7)


# ── Public interface (matches generate_robot.py) ─────────────────────────────

def robot_frame(t: float, mouth_open: float, glow: float,
                pose: str = 'neutral', bob: int = 0) -> Image.Image:
    img  = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    raised = pose == 'shrug'

    _hair_back(draw)
    _body(draw)
    _ears(draw)
    _face(draw)
    _hair_front(draw)
    _brows(draw, raised=raised)
    _nose(draw)
    _eyes(draw, t, glow)
    _mouth(draw, mouth_open)

    # Subtle sway + bob offset
    sway = int(4 * math.sin(t * math.pi * 0.72))
    if bob != 0 or sway != 0:
        out = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        out.paste(img, (sway, bob), img)
        return out
    return img
