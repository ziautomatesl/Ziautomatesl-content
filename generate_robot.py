"""
High-quality 3D robot renderer using numpy ray-based sphere shading.
- Metallic blue material with diffuse + specular + rim lighting
- Chibi proportions (big head, compact body) like the mascot
- Gesture system: neutral, wave, point, explain, thumbsup
- Animated face: mouth open/close, eye glow
"""
import math
import numpy as np
from PIL import Image, ImageDraw

RW, RH = 860, 980

# ── Material colours ─────────────────────────────────────────────────────────
BLUE   = (18,  52, 210)
BLUE2  = (14,  42, 185)
METAL  = (32,  48,  88)
DARK   = (10,  14,  28)
ORANGE = (235, 128,   8)
VISOR  = (7,    7,  17)
CYAN   = (0,  215, 255)
FOOT   = (12,  12,  24)

LIGHT  = np.array([0.44, -0.50, 0.74])   # main light direction
RIM    = np.array([-0.6,   0.0, 0.80])   # rim (back) light


# ── Core 3-D primitive ────────────────────────────────────────────────────────
def _sphere(out, cx, cy, r, col,
            sp_pow=38, sp_str=0.95, rim_str=0.38, rim_col=None):
    if rim_col is None:
        rim_col = (0, 80, 180)
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-r-1), min(H, cy+r+2)
    x0, x1 = max(0, cx-r-1), min(W, cx+r+2)
    ys, xs  = np.mgrid[y0:y1, x0:x1]
    dx = (xs-cx)/r;  dy = (ys-cy)/r
    d2 = dx*dx + dy*dy
    ok = d2 <= 1.0
    dz = np.where(ok, np.sqrt(np.clip(1-d2, 0, 1)), 0)

    dot  = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diff = np.where(ok, np.clip(dot, 0.10, 1.0), 0)
    spec = np.where(ok, np.clip(2*dz*dot - LIGHT[2], 0, 1)**sp_pow * sp_str, 0)
    rim  = np.where(ok, (1.0 - dz)**5 * rim_str, 0)

    for i, c in enumerate(col):
        ch = np.clip(c*diff + 255*spec + rim_col[i]*rim, 0, 255)
        out[y0:y1, x0:x1, i] = np.where(ok, ch, out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(ok, 255, out[y0:y1, x0:x1, 3])


def _ellipsoid(out, cx, cy, rx, ry, col, **kw):
    if rx <= 0 or ry <= 0:
        return
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-ry-1), min(H, cy+ry+2)
    x0, x1 = max(0, cx-rx-1), min(W, cx+rx+2)
    ys, xs  = np.mgrid[y0:y1, x0:x1]
    dx = (xs-cx)/rx; dy = (ys-cy)/ry
    d2 = dx*dx + dy*dy
    ok = d2 <= 1.0
    dz = np.where(ok, np.sqrt(np.clip(1-d2, 0, 1)), 0)
    dot  = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diff = np.where(ok, np.clip(dot, 0.10, 1.0), 0)
    sp_pow = kw.get('sp_pow', 28); sp_str = kw.get('sp_str', 0.70)
    rim_str = kw.get('rim_str', 0.28)
    rim_col = kw.get('rim_col', (0, 60, 160))
    spec = np.where(ok, np.clip(2*dz*dot - LIGHT[2], 0, 1)**sp_pow * sp_str, 0)
    rim  = np.where(ok, (1.0-dz)**5 * rim_str, 0)
    for i, c in enumerate(col):
        ch = np.clip(c*diff + 255*spec + rim_col[i]*rim, 0, 255)
        out[y0:y1, x0:x1, i] = np.where(ok, ch, out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(ok, 255, out[y0:y1, x0:x1, 3])


def _chain(out, x1, y1, x2, y2, r, col, n=None, **kw):
    """Draw a rounded cylinder as a chain of spheres."""
    dist = math.hypot(x2-x1, y2-y1)
    if dist == 0:
        return
    n = n or max(3, int(dist / (r*0.55)))
    for i in range(n+1):
        t  = i/n
        cx = int(x1 + t*(x2-x1))
        cy = int(y1 + t*(y2-y1))
        sr = max(2, int(r*(1 - 0.18*t)))
        _sphere(out, cx, cy, sr, col, **kw)


# ── Arm poses: (upper_arm_angle_deg, forearm_relative_deg) ───────────────────
# angle 0 = straight up, 90 = horizontal right, 180 = down
POSES = {
    'neutral':   {'r': (75, 30),  'l': (108, -20)},  # right arm slightly up, left down
    'wave':      {'r': (38, 55),  'l': (110, -18)},  # right arm high, waving
    'explain':   {'r': (88, 15),  'l': (92,   15)},  # both spread open
    'point_cam': {'r': (92,  0),  'l': (110, -18)},  # right arm horizontal →camera
    'thumbsup':  {'r': (62, -10), 'l': (110, -18)},  # fist raised
    'shrug':     {'r': (55, 30),  'l': (55,   30)},  # both raised sideways
}


def _arm_coords(cx, shoulder_y, angle_deg, forearm_deg, side='r'):
    """Return (shoulder, elbow, hand) pixel coords for an arm."""
    sign  = 1 if side == 'r' else -1
    sx    = cx + sign * 172
    sy    = shoulder_y
    ang1  = math.radians(angle_deg)
    ux    = sx + sign * math.sin(ang1) * 115
    uy    = sy - math.cos(ang1) * 115
    ang2  = math.radians(angle_deg + forearm_deg)
    hx    = ux + sign * math.sin(ang2) * 100
    hy    = uy - math.cos(ang2) * 100
    return (int(sx), int(sy)), (int(ux), int(uy)), (int(hx), int(hy))


# ── Build the static robot (no face / no arms) ───────────────────────────────
def _build_static(cx, head_cy, body_cy):
    arr = np.zeros((RH, RW, 4), dtype=np.float32)

    # Feet
    _ellipsoid(arr, cx-92,  RH-52, 65, 34, FOOT, sp_pow=14, sp_str=0.3)
    _ellipsoid(arr, cx+92,  RH-52, 65, 34, FOOT, sp_pow=14, sp_str=0.3)

    # Legs
    _chain(arr, cx-88, body_cy+130, cx-90, RH-80, 38, BLUE2,
           sp_pow=22, rim_str=0.30)
    _chain(arr, cx+88, body_cy+130, cx+90, RH-80, 38, BLUE2,
           sp_pow=22, rim_str=0.30)

    # Body
    _ellipsoid(arr, cx, body_cy, 165, 152, BLUE,
               sp_pow=26, sp_str=0.80, rim_str=0.35)

    # Waist ring
    _ellipsoid(arr, cx, body_cy+130, 148, 24, METAL,
               sp_pow=18, sp_str=0.55, rim_str=0.20)

    # Chest glow base (will be overlaid per-frame)
    _sphere(arr, cx, body_cy-18, 38, (0, 45, 140),
            sp_pow=14, sp_str=0.30, rim_str=0.10)

    # Neck
    _chain(arr, cx, head_cy+152, cx, body_cy-148, 26, METAL,
           sp_pow=18, rim_str=0.18)

    # Head sphere (render last to be on top)
    _sphere(arr, cx, head_cy, 168, BLUE,
            sp_pow=40, sp_str=1.0, rim_str=0.42,
            rim_col=(0, 90, 200))

    # Antenna stick
    _chain(arr, cx, head_cy-165, cx, head_cy-218, 6, METAL, n=5)
    # Antenna ball
    _sphere(arr, cx, head_cy-228, 24, ORANGE,
            sp_pow=44, sp_str=1.0, rim_col=(200, 80, 0))

    return arr


# ── Pre-render base (called once at module load) ──────────────────────────────
_CX       = RW // 2
_HEAD_CY  = 240
_BODY_CY  = 570
_BASE_ARR = _build_static(_CX, _HEAD_CY, _BODY_CY)

META = {
    'cx': _CX, 'head_cy': _HEAD_CY, 'body_cy': _BODY_CY,
    'shoulder_y': _BODY_CY - 148,
    # Face (proportional to head)
    'visor_cx':  _CX,     'visor_cy':  _HEAD_CY + 10,
    'visor_rw':  108,     'visor_rh':  92,
    'eye_lx':   _CX-50,  'eye_rx':    _CX+50,
    'eye_y':    _HEAD_CY - 8,
    'eye_rw':    34,      'eye_rh':    23,
    'mouth_cx':  _CX,     'mouth_cy':  _HEAD_CY + 78,
    'mouth_rw':  55,      'mouth_rh':  14,
}


# ── Per-frame render ──────────────────────────────────────────────────────────
def robot_frame(t: float, mouth_open: float, glow: float,
                pose: str = 'neutral', bob: int = 0) -> Image.Image:
    """
    Full robot frame.
    t          : time in seconds (for wave oscillation etc.)
    mouth_open : 0=smile 1=fully open
    glow       : 0=dim  1=blazing
    pose       : key in POSES dict
    bob        : vertical pixel offset
    """
    arr = _BASE_ARR.copy()
    cx   = META['cx']
    sho  = META['shoulder_y']

    # Dynamic chest glow
    g = glow
    glow_col = (0, int(70 + 150*g), int(160 + 95*g))
    _sphere(arr, cx, META['body_cy']-18, int(28 + g*18), glow_col,
            sp_pow=12, sp_str=0.25, rim_str=0.08)

    # ── Arms ──────────────────────────────────────────────────────────────────
    p = POSES.get(pose, POSES['neutral'])

    # Wave oscillation for right arm in 'wave' or 'neutral'
    wave_offset = int(8 * math.sin(t * math.pi * 3.2)) if pose == 'wave' else 0

    # Left arm
    la, le, lh = _arm_coords(cx, sho + wave_offset//2,
                              p['l'][0], p['l'][1], 'l')
    _chain(arr, la[0], la[1], le[0], le[1], 34, BLUE, sp_pow=26, rim_str=0.32)
    _chain(arr, le[0], le[1], lh[0], lh[1], 28, BLUE2, sp_pow=24, rim_str=0.28)
    _sphere(arr, lh[0], lh[1], 30, BLUE2, sp_pow=22, rim_str=0.25)  # fist

    # Right arm
    ra, re, rh = _arm_coords(cx, sho + wave_offset,
                              p['r'][0], p['r'][1], 'r')
    _chain(arr, ra[0], ra[1], re[0], re[1], 34, BLUE, sp_pow=26, rim_str=0.32)
    _chain(arr, re[0], re[1], rh[0], rh[1], 28, BLUE2, sp_pow=24, rim_str=0.28)
    _sphere(arr, rh[0], rh[1], 30, BLUE2, sp_pow=22, rim_str=0.25)

    # Shoulders
    _sphere(arr, cx-172, sho, 42, METAL, sp_pow=20, rim_str=0.22)
    _sphere(arr, cx+172, sho, 42, METAL, sp_pow=20, rim_str=0.22)

    # ── Face overlay ──────────────────────────────────────────────────────────
    img  = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(img)

    vcx, vcy = META['visor_cx'], META['visor_cy']
    vrw, vrh = META['visor_rw'], META['visor_rh']

    # Visor
    draw.ellipse([(vcx-vrw, vcy-vrh), (vcx+vrw, vcy+vrh)],
                 fill=VISOR+(255,))

    # Eye glow halos
    gv = min(255, int(140 + 115*g))
    bv = min(255, int(195 + 60*g))
    ECYAN  = (0, gv, bv, 255)
    EHALO  = (0, int(40+60*g), int(70+60*g), 255)
    for ex in (META['eye_lx'], META['eye_rx']):
        ey  = META['eye_y']
        erw = META['eye_rw']; erh = META['eye_rh']
        draw.ellipse([(ex-erw-7, ey-erh-6), (ex+erw+7, ey+erh+6)], fill=EHALO)
        draw.ellipse([(ex-erw,   ey-erh),   (ex+erw,   ey+erh)],   fill=ECYAN)
        draw.ellipse([(ex-erw//3, ey-erh//2), (ex+erw//4, ey+2)],
                     fill=(220, 235, 255, 200))

    # Mouth
    mcx, mcy = META['mouth_cx'], META['mouth_cy']
    mrw, mrh = META['mouth_rw'], META['mouth_rh']
    cover_h  = mrh * 4
    draw.ellipse([(mcx-mrw-8, mcy-cover_h), (mcx+mrw+8, mcy+cover_h)],
                 fill=VISOR+(255,))

    if mouth_open < 0.07:
        draw.arc([(mcx-mrw, mcy-mrw//3), (mcx+mrw, mcy+mrw//3)],
                 start=8, end=172, fill=ECYAN, width=5)
        draw.ellipse([(mcx-mrw-2, mcy-4), (mcx-mrw+7, mcy+5)], fill=ECYAN)
        draw.ellipse([(mcx+mrw-7, mcy-4), (mcx+mrw+2, mcy+5)], fill=ECYAN)
    else:
        ow = int(mrw * 0.88)
        oh = int(5 + mouth_open * mrw * 0.60)
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)],
                     fill=VISOR+(255,))
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)],
                     outline=ECYAN, width=4)
        if mouth_open > 0.28:
            tw = int(ow*0.62)
            draw.arc([(mcx-tw, mcy-oh+3), (mcx+tw, mcy-oh//2+5)],
                     start=2, end=178,
                     fill=(200, 215, 235, 200), width=3)

    # ── Bob offset ────────────────────────────────────────────────────────────
    if bob != 0:
        final = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        final.paste(img, (0, bob), img)
        return final
    return img
