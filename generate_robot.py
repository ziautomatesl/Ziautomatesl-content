"""
3D robot avatar generated with numpy sphere rendering + PIL drawing.
Looks similar to the ziautomate blue robot mascot.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

# Canvas for the robot
RW, RH = 820, 960
LIGHT = (0.42, -0.52, 0.74)   # light direction (x, y, z)

BLUE_HEAD  = (18,  55, 205)
BLUE_BODY  = (15,  45, 185)
BLUE_LIMB  = (20,  50, 175)
ORANGE     = (230, 130,  10)
DARK_VISOR = (8,    8,  18)
CYAN_EYE   = (0,  210, 255)
FOOT_COLOR = (14,  14,  28)


# ── 3D sphere via numpy ───────────────────────────────────────────────────────
def _sphere(out, cx, cy, r, base, spec_power=32, spec_str=0.9):
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-r-1), min(H, cy+r+2)
    x0, x1 = max(0, cx-r-1), min(W, cx+r+2)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    dx = (xs - cx) / r
    dy = (ys - cy) / r
    d2 = dx**2 + dy**2
    inside = d2 <= 1.0
    dz = np.where(inside, np.sqrt(np.clip(1 - d2, 0, 1)), 0)
    dot = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diffuse = np.where(inside, np.clip(dot, 0.12, 1.0), 0)
    spec = np.where(inside, np.clip(2*dz*dot - LIGHT[2], 0, 1)**spec_power * spec_str, 0)
    for i, c in enumerate(base):
        channel = np.clip(c * diffuse + 255 * spec, 0, 255)
        out[y0:y1, x0:x1, i] = np.where(inside, channel, out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(inside, 255, out[y0:y1, x0:x1, 3])


def _ellipsoid(out, cx, cy, rx, ry, base, spec_power=28, spec_str=0.7):
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-ry-1), min(H, cy+ry+2)
    x0, x1 = max(0, cx-rx-1), min(W, cx+rx+2)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    dx = (xs - cx) / rx
    dy = (ys - cy) / ry
    d2 = dx**2 + dy**2
    inside = d2 <= 1.0
    dz = np.where(inside, np.sqrt(np.clip(1 - d2, 0, 1)), 0)
    dot = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diffuse = np.where(inside, np.clip(dot, 0.12, 1.0), 0)
    spec = np.where(inside, np.clip(2*dz*dot - LIGHT[2], 0, 1)**spec_power * spec_str, 0)
    for i, c in enumerate(base):
        channel = np.clip(c * diffuse + 255 * spec, 0, 255)
        out[y0:y1, x0:x1, i] = np.where(inside, channel, out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(inside, 255, out[y0:y1, x0:x1, 3])


# ── Pre-render static robot parts ────────────────────────────────────────────
def build_base():
    """Render the robot (no mouth/eyes) as a pre-computed numpy RGBA array."""
    arr = np.zeros((RH, RW, 4), dtype=np.float32)
    cx = RW // 2

    # Feet
    _ellipsoid(arr, cx-90, 900, 62, 32, FOOT_COLOR)
    _ellipsoid(arr, cx+90, 900, 62, 32, FOOT_COLOR)

    # Legs
    _ellipsoid(arr, cx-88, 790, 42, 90, BLUE_LIMB)
    _ellipsoid(arr, cx+88, 790, 42, 90, BLUE_LIMB)

    # Body
    _ellipsoid(arr, cx, 580, 168, 148, BLUE_BODY, spec_power=24, spec_str=0.8)

    # Chest glow placeholder (filled later in overlay)
    _sphere(arr, cx, 560, 40, (0, 60, 180), spec_power=16, spec_str=0.4)

    # Shoulders
    _sphere(arr, cx-175, 465, 45, BLUE_LIMB, spec_power=20)
    _sphere(arr, cx+175, 465, 45, BLUE_LIMB, spec_power=20)

    # Left arm (hanging, slightly forward)
    _ellipsoid(arr, cx-200, 585, 36, 110, BLUE_LIMB)
    _sphere(arr, cx-195, 700, 36, BLUE_LIMB, spec_power=18)   # fist

    # Right arm — raised and waving
    _ellipsoid(arr, cx+215, 490, 36, 80, BLUE_LIMB)
    _ellipsoid(arr, cx+268, 360, 32, 72, BLUE_LIMB)
    _sphere(arr, cx+310, 275, 36, BLUE_LIMB, spec_power=18)   # fist raised

    # Neck
    _ellipsoid(arr, cx, 388, 28, 45, BLUE_LIMB)

    # Head (sphere) — drawn last so it's on top
    _sphere(arr, cx, 218, 162, BLUE_HEAD, spec_power=36, spec_str=1.0)

    # Antenna stick
    for y in range(40, 68):
        arr[y, cx-2:cx+3, :3] = [80, 80, 80]
        arr[y, cx-2:cx+3, 3] = 255
    # Antenna ball
    _sphere(arr, cx, 38, 22, ORANGE, spec_power=40, spec_str=1.0)

    # Face visor (dark oval on front of head)
    img = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(img)
    vx, vy, vrx, vry = cx, 225, 105, 88
    draw.ellipse([(vx-vrx, vy-vry), (vx+vrx, vy+vry)],
                 fill=DARK_VISOR + (255,))

    return np.array(img).astype(np.float32), {
        'cx': cx,
        'head_cy': 218,
        'visor_cx': vx, 'visor_cy': vy,
        'eye_ly': vy - 20,  'eye_lx': vx - 48,
        'eye_ry': vy - 20,  'eye_rx': vx + 48,
        'eye_rw': 32,       'eye_rh': 22,
        'mouth_cx': vx,     'mouth_cy': vy + 46,
        'mouth_rw': 52,     'mouth_rh': 16,
    }


BASE_ARR, META = build_base()


# ── Per-frame animated render ─────────────────────────────────────────────────
def robot_frame(mouth_open: float, glow: float, bob: int = 0) -> Image.Image:
    """
    mouth_open : 0.0 smile closed  →  1.0 fully open
    glow       : 0.0 dim           →  1.0 blazing cyan
    bob        : vertical pixel offset (animation)
    Returns PIL RGBA image.
    """
    arr = BASE_ARR.copy()

    m = META
    g = glow
    CYAN  = (0, min(255, int(170 + 85*g)), min(255, int(215 + 40*g)), 255)
    CYAND = (0, int(40 + 50*g), int(70 + 50*g), 255)
    WHITE = (220, 235, 255, 255)
    DARK  = DARK_VISOR + (255,)

    img  = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(img)

    # ── Chest core glow ───────────────────────────────────────────────────────
    cr = int(24 + g * 14)
    draw.ellipse([(m['cx']-cr, 560-cr), (m['cx']+cr, 560+cr)],
                 fill=(0, int(80 + 120*g), int(170 + 85*g), 255))
    draw.ellipse([(m['cx']-cr//2, 560-cr//2), (m['cx']+cr//2, 560+cr//2)],
                 fill=(int(180*g), int(220*g), 255, 255))

    # ── Eyes ─────────────────────────────────────────────────────────────────
    for (ex, ey) in ((m['eye_lx'], m['eye_ly']), (m['eye_rx'], m['eye_ry'])):
        erw, erh = m['eye_rw'], m['eye_rh']
        # Glow halo
        draw.ellipse([(ex-erw-6, ey-erh-5), (ex+erw+6, ey+erh+5)], fill=CYAND)
        # Iris
        draw.ellipse([(ex-erw, ey-erh), (ex+erw, ey+erh)], fill=CYAN)
        # Specular
        draw.ellipse([(ex-erw//3, ey-erh//2), (ex+erw//4, ey)], fill=WHITE)

    # ── Mouth ─────────────────────────────────────────────────────────────────
    mcx, mcy = m['mouth_cx'], m['mouth_cy']
    mrw, mrh = m['mouth_rw'], m['mouth_rh']

    # Cover existing area
    draw.ellipse([(mcx-mrw-6, mcy-mrh-8), (mcx+mrw+6, mcy+mrh+8)], fill=DARK)

    if mouth_open < 0.08:
        # Closed smile arc
        draw.arc([(mcx-mrw, mcy-mrw//3), (mcx+mrw, mcy+mrw//3)],
                 start=8, end=172, fill=CYAN, width=5)
        # Smile corners
        draw.ellipse([(mcx-mrw-3, mcy-5), (mcx-mrw+6, mcy+6)], fill=CYAN)
        draw.ellipse([(mcx+mrw-6, mcy-5), (mcx+mrw+3, mcy+6)], fill=CYAN)
    else:
        # Open mouth oval
        ow = int(mrw * 0.88)
        oh = int(6 + mouth_open * mrw * 0.58)
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)],
                     fill=(5, 5, 15, 255))
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)],
                     outline=CYAN, width=4)
        if mouth_open > 0.3:
            tw = int(ow * 0.65)
            draw.arc([(mcx-tw, mcy-oh+3), (mcx+tw, mcy-oh//2+4)],
                     start=0, end=180, fill=(200, 215, 230, 180), width=3)

    # ── Apply vertical bob ────────────────────────────────────────────────────
    if bob != 0:
        final = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        final.paste(img, (0, bob), img)
        return final

    return img
