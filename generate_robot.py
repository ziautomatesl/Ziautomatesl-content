"""
ZIA – Cinematic 3D robot. Full procedural animation.

Every joint is driven by overlapping sine curves – no pose states, no A→B snapping.
Gestures shift the *mean* of continuous curves; offset-fade removes any jump.
Head moves independently from body. Arms have organic inertia-like ebb and flow.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RW, RH = 960, 980

# ── Palette ───────────────────────────────────────────────────────────────────
BLUE   = (18,  52, 210)
BLUE2  = (14,  42, 185)
METAL  = (32,  48,  88)
ORANGE = (235, 128,   8)
VISOR  = (7,    7,  17)
CYAN   = (0,  215, 255)
FOOT   = (12,  12,  24)
PANEL  = (20,  30,  64)

LIGHT  = np.array([0.44, -0.50, 0.74])


# ── 3-D primitives (numpy sphere / ellipsoid / chain) ─────────────────────────
def _sphere(out, cx, cy, r, col,
            sp_pow=38, sp_str=0.95, rim_str=0.38, rim_col=None):
    if r < 1:
        return
    if rim_col is None:
        rim_col = (0, 80, 180)
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-r-1), min(H, cy+r+2)
    x0, x1 = max(0, cx-r-1), min(W, cx+r+2)
    ys, xs  = np.mgrid[y0:y1, x0:x1]
    dx = (xs-cx)/r;  dy = (ys-cy)/r
    d2 = dx*dx + dy*dy;  ok = d2 <= 1.0
    dz   = np.where(ok, np.sqrt(np.clip(1-d2, 0, 1)), 0)
    dot  = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diff = np.where(ok, np.clip(dot, 0.10, 1.0), 0)
    spec = np.where(ok, np.clip(2*dz*dot - LIGHT[2], 0, 1)**sp_pow * sp_str, 0)
    rim  = np.where(ok, (1.0 - dz)**5 * rim_str, 0)
    for i, c in enumerate(col):
        out[y0:y1, x0:x1, i] = np.where(
            ok, np.clip(c*diff + 255*spec + rim_col[i]*rim, 0, 255),
            out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(ok, 255, out[y0:y1, x0:x1, 3])


def _ellipsoid(out, cx, cy, rx, ry, col, **kw):
    if rx <= 0 or ry <= 0:
        return
    H, W = out.shape[:2]
    y0, y1 = max(0, cy-ry-1), min(H, cy+ry+2)
    x0, x1 = max(0, cx-rx-1), min(W, cx+rx+2)
    ys, xs  = np.mgrid[y0:y1, x0:x1]
    dx = (xs-cx)/rx;  dy = (ys-cy)/ry
    d2 = dx*dx + dy*dy;  ok = d2 <= 1.0
    dz   = np.where(ok, np.sqrt(np.clip(1-d2, 0, 1)), 0)
    dot  = np.clip(dx*LIGHT[0] + dy*LIGHT[1] + dz*LIGHT[2], 0, 1)
    diff = np.where(ok, np.clip(dot, 0.10, 1.0), 0)
    sp_pow  = kw.get('sp_pow', 28);  sp_str  = kw.get('sp_str',  0.70)
    rim_str = kw.get('rim_str', 0.28); rim_col = kw.get('rim_col', (0, 60, 160))
    spec = np.where(ok, np.clip(2*dz*dot - LIGHT[2], 0, 1)**sp_pow * sp_str, 0)
    rim  = np.where(ok, (1.0-dz)**5 * rim_str, 0)
    for i, c in enumerate(col):
        out[y0:y1, x0:x1, i] = np.where(
            ok, np.clip(c*diff + 255*spec + rim_col[i]*rim, 0, 255),
            out[y0:y1, x0:x1, i])
    out[y0:y1, x0:x1, 3] = np.where(ok, 255, out[y0:y1, x0:x1, 3])


def _chain(out, x1, y1, x2, y2, r, col, n=None, **kw):
    dist = math.hypot(x2-x1, y2-y1)
    if dist == 0:
        return
    n = n or max(3, int(dist / (r*0.55)))
    for i in range(n+1):
        tt = i/n
        _sphere(out, int(x1+tt*(x2-x1)), int(y1+tt*(y2-y1)),
                max(2, int(r*(1-0.18*tt))), col, **kw)


# ── Procedural arm curves ─────────────────────────────────────────────────────
# Idle micro-oscillations (different freq/phase per joint so motion is organic)
def _oi(t): return 7*math.sin(t*math.pi*1.10+0.50) + 3*math.sin(t*math.pi*2.30+1.80)
def _of(t): return 5*math.sin(t*math.pi*1.70+1.20) + 2*math.sin(t*math.pi*3.10+2.50)
def _ol(t): return 5*math.sin(t*math.pi*0.90+2.10) + 2*math.sin(t*math.pi*1.80+3.50)
def _olf(t): return 3*math.sin(t*math.pi*1.40+1.80) + 2*math.sin(t*math.pi*2.70+0.90)


def _gesture_curves(t, gesture, glow, energy=1.0):
    """
    Pure function of t, gesture, glow and energy.
    energy < 1 → smaller/slower movement (pre-gesture stillness)
    energy > 1 → bigger/faster movement (emphasis/burst)
    """
    te = t * (0.82 + 0.18 * energy)   # subtle time-warp: faster at high energy
    b  = (1.0 + 0.55 * glow) * energy

    if gesture == 'wave':
        w = 20 * math.sin(te*math.pi*3.5) * b + 5*math.sin(te*math.pi*7.1+0.5)
        return (42 + w + 4*math.sin(te*math.pi*1.0+0.5),
                50 + w*0.55 + 3*math.sin(te*math.pi*1.6+1.1),
                106 + _ol(te),
                -16 + _olf(te))

    if gesture == 'explain':
        return (88 + 7*math.sin(te*math.pi*1.5+0.4)*b + _oi(te)*0.35,
                14 + 6*math.sin(te*math.pi*2.1+0.9)*b + _of(te)*0.30,
                90 + 7*math.sin(te*math.pi*1.3+1.5)*b + _ol(te)*0.35,
                14 + 5*math.sin(te*math.pi*1.9+2.0)*b + _olf(te)*0.30)

    if gesture == 'point_cam':
        return (90 + 3*math.sin(te*math.pi*1.2+0.3)*b + _oi(te)*0.15,
                 0 + 2*math.sin(te*math.pi*1.8+0.8)*b,
               108 + _ol(te),
               -16 + _olf(te))

    if gesture == 'thumbsup':
        return (60 + 7*math.sin(te*math.pi*1.3+0.6)*b + _oi(te)*0.45,
               -13 + 5*math.sin(te*math.pi*1.7+0.4)*b + _of(te)*0.25,
               108 + _ol(te),
               -16 + _olf(te))

    if gesture == 'shrug':
        s = 10*math.sin(te*math.pi*0.9+0.5)*b
        return (52 + s + _oi(te)*0.55,
                30 + 7*math.sin(te*math.pi*1.2+1.2)*b,
                52 + s + _ol(te)*0.55,
                30 + 6*math.sin(te*math.pi*1.1+2.4)*b)

    # neutral
    return (76 + _oi(te)*b*0.80,  27 + _of(te)*b*0.80,
           105 + _ol(te)*b*0.70, -17 + _olf(te)*b*0.70)


# ── Seamless transition (offset-fade, no state machine) ──────────────────────
def _smooth(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3.0 - 2.0*x)   # smoothstep


_gt = {'cur': 'neutral', 'at': -99.0,
       'dru': 0.0, 'drf': 0.0, 'dlu': 0.0, 'dlf': 0.0}


def _arm_angles(t, gesture, glow, energy=1.0):
    """
    Seamless gesture transitions: record delta at switch moment, fade with smoothstep.
    energy scales all oscillation amplitude and slightly warps time.
    """
    if gesture != _gt['cur']:
        old = _gesture_curves(t, _gt['cur'], glow, energy)
        new = _gesture_curves(t, gesture,    glow, energy)
        _gt['dru'] = old[0] - new[0]
        _gt['drf'] = old[1] - new[1]
        _gt['dlu'] = old[2] - new[2]
        _gt['dlf'] = old[3] - new[3]
        _gt['cur'] = gesture
        _gt['at']  = t

    fade = 1.0 - _smooth((t - _gt['at']) / 0.42)
    ru, rf, lu, lf = _gesture_curves(t, gesture, glow, energy)
    return (ru + _gt['dru']*fade, rf + _gt['drf']*fade,
            lu + _gt['dlu']*fade, lf + _gt['dlf']*fade)


def _arm_coords(cx, sy, angle, forearm, side):
    sign = 1 if side == 'r' else -1
    sx   = cx + sign*168
    a1   = math.radians(angle)
    ux   = sx + sign*math.sin(a1)*110
    uy   = sy - math.cos(a1)*110
    a2   = math.radians(angle + forearm)
    hx   = ux + sign*math.sin(a2)*95
    hy   = uy - math.cos(a2)*95
    return (int(sx), int(sy)), (int(ux), int(uy)), (int(hx), int(hy))


# ── Static base: lower body only (head/neck rendered per-frame for indie movement)
_CX      = RW // 2
_HEAD_CY = 240
_BODY_CY = 620


def _build_static(cx, body_cy):
    arr = np.zeros((RH, RW, 4), dtype=np.float32)
    # Hover pads
    _ellipsoid(arr, cx-92, RH-55, 72, 26, FOOT, sp_pow=12, sp_str=0.22)
    _ellipsoid(arr, cx+92, RH-55, 72, 26, FOOT, sp_pow=12, sp_str=0.22)
    # Legs
    _chain(arr, cx-88, body_cy+130, cx-90, RH-78, 36, BLUE2, sp_pow=22, rim_str=0.28)
    _chain(arr, cx+88, body_cy+130, cx+90, RH-78, 36, BLUE2, sp_pow=22, rim_str=0.28)
    # Body
    _ellipsoid(arr, cx, body_cy, 165, 145, BLUE, sp_pow=28, sp_str=0.88, rim_str=0.40)
    # Panel detail lines
    _ellipsoid(arr, cx-56, body_cy-18, 13, 56, PANEL, sp_pow=8, sp_str=0.15, rim_str=0.04)
    _ellipsoid(arr, cx+56, body_cy-18, 13, 56, PANEL, sp_pow=8, sp_str=0.15, rim_str=0.04)
    # Waist ring
    _ellipsoid(arr, cx, body_cy+130, 148, 22, METAL, sp_pow=18, sp_str=0.55, rim_str=0.20)
    return arr


_BASE_ARR = _build_static(_CX, _BODY_CY)


# ── Per-frame render ──────────────────────────────────────────────────────────
def robot_frame(t: float, mouth_open: float, glow: float,
                pose: str = 'neutral', bob: int = 0,
                gaze_x: float = 0.0, gaze_y: float = 0.0,
                energy: float = 1.0) -> Image.Image:
    arr = _BASE_ARR.copy()
    cx  = _CX;  g = glow
    sho = _BODY_CY - 145

    # ── Independent head position (organic motion + gaze bias) ────────────────
    hdy = (6.0*math.sin(t*math.pi*1.30+0.30)
         + 3.0*math.sin(t*math.pi*2.10+0.80)
         + 1.5*math.sin(t*math.pi*3.70+1.50)) * (1.0 + 0.35*g)
    hdx = (3.0*math.sin(t*math.pi*0.70+1.20)
         + 1.5*math.sin(t*math.pi*1.40+2.80))
    # Gaze biases head orientation: look left/right/up smoothly
    hx  = int(cx + hdx + gaze_x * 7)
    hy  = int(_HEAD_CY + hdy + gaze_y * 5)

    # ── Neck (follows head so it angles naturally) ────────────────────────────
    _chain(arr, hx, hy+148, cx, _BODY_CY-142, 24, METAL, sp_pow=18, rim_str=0.18)

    # ── Pulsing chest core ────────────────────────────────────────────────────
    pulse = 0.5 + 0.5*math.sin(t*math.pi*4.6)
    gc    = (0,
             int(65 + 155*(g*0.65 + pulse*0.35*g)),
             int(155 + 100*g))
    _sphere(arr, cx, _BODY_CY-18, int(26+g*22), gc,
            sp_pow=12, sp_str=0.25, rim_str=0.08)

    # ── Head assembly (ear fins → head → antenna) ─────────────────────────────
    _ellipsoid(arr, hx-175, hy, 15, 40, METAL, sp_pow=18, sp_str=0.55, rim_str=0.18)
    _ellipsoid(arr, hx+175, hy, 15, 40, METAL, sp_pow=18, sp_str=0.55, rim_str=0.18)
    _sphere(arr, hx, hy, 180, BLUE,
            sp_pow=42, sp_str=1.05, rim_str=0.46, rim_col=(0, 90, 200))
    ant_cy = hy - 236
    _chain(arr, hx, hy-176, hx, ant_cy, 6, METAL, n=5)
    ant_r  = int(23 + 6*math.sin(t*math.pi*2.6))
    _sphere(arr, hx, ant_cy, ant_r, ORANGE,
            sp_pow=46, sp_str=1.05, rim_col=(200, 80, 0))

    # ── Shoulders + continuously animated arms ────────────────────────────────
    _sphere(arr, cx-168, sho, 44, METAL, sp_pow=22, rim_str=0.24)
    _sphere(arr, cx+168, sho, 44, METAL, sp_pow=22, rim_str=0.24)

    ru, rf, lu, lf = _arm_angles(t, pose, g, energy)

    la, le, lh = _arm_coords(cx, sho, lu, lf, 'l')
    _chain(arr, la[0], la[1], le[0], le[1], 34, BLUE,  sp_pow=26, rim_str=0.32)
    _chain(arr, le[0], le[1], lh[0], lh[1], 28, BLUE2, sp_pow=24, rim_str=0.28)
    _sphere(arr, lh[0], lh[1], 30, BLUE2, sp_pow=22, rim_str=0.25)

    ra, re, rh = _arm_coords(cx, sho, ru, rf, 'r')
    _chain(arr, ra[0], ra[1], re[0], re[1], 34, BLUE,  sp_pow=26, rim_str=0.32)
    _chain(arr, re[0], re[1], rh[0], rh[1], 28, BLUE2, sp_pow=24, rim_str=0.28)
    _sphere(arr, rh[0], rh[1], 30, BLUE2, sp_pow=22, rim_str=0.25)

    # ── PIL face overlay (all coords relative to live head position) ──────────
    img  = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(img)

    vcx, vcy = hx,  hy + 10
    vrw, vrh = 112, 95

    # Visor background
    draw.ellipse([(vcx-vrw, vcy-vrh), (vcx+vrw, vcy+vrh)], fill=VISOR+(255,))

    # Animated scan lines
    scan_off = int((t * 30) % 10)
    for sy in range(vcy - vrh + scan_off, vcy + vrh, 10):
        dv = (sy - vcy) / vrh
        hw = int(vrw * math.sqrt(max(0.0, 1.0 - dv*dv)) - 6)
        if hw > 0:
            draw.line([(vcx-hw, sy), (vcx+hw, sy)], fill=(0, 28, 48, 155), width=1)

    # Glass reflection
    draw.arc([(vcx-vrw+18, vcy-vrh+6), (vcx-8, vcy-8)],
             start=215, end=308, fill=(38, 75, 115, 130), width=3)

    # Eye glow
    gv    = min(255, int(145 + 110*g))
    bv    = min(255, int(195 +  60*g))
    ECYAN = (0, gv, bv, 255)
    EHALO = (0, int(38+65*g), int(68+65*g), 255)
    # Gaze offsets the pupil highlight so the robot visibly looks in a direction
    gdx = int(gaze_x * 13)
    gdy = int(gaze_y *  8)
    for ex in (hx-52, hx+52):
        ey = hy - 10;  erw = 36;  erh = 24
        draw.ellipse([(ex-erw-8, ey-erh-7), (ex+erw+8, ey+erh+7)], fill=EHALO)
        draw.ellipse([(ex-erw,   ey-erh),   (ex+erw,   ey+erh)],   fill=ECYAN)
        draw.ellipse([(ex-erw//3+gdx, ey-erh//2+gdy),
                      (ex+erw//4+gdx, ey+2+gdy)],
                     fill=(225, 238, 255, 200))

    # Mouth (cover + animate)
    mcx, mcy = hx, hy + 80
    mrw, mrh = 56, 14
    cover_h  = min(mrh * 4, vcy + vrh - mcy - 2)
    draw.ellipse([(mcx-mrw-8, mcy-cover_h), (mcx+mrw+8, mcy+cover_h)],
                 fill=VISOR+(255,))
    if mouth_open < 0.07:
        draw.arc([(mcx-mrw, mcy-mrw//3), (mcx+mrw, mcy+mrw//3)],
                 start=8, end=172, fill=ECYAN, width=5)
        draw.ellipse([(mcx-mrw-2, mcy-4), (mcx-mrw+7, mcy+5)], fill=ECYAN)
        draw.ellipse([(mcx+mrw-7, mcy-4), (mcx+mrw+2, mcy+5)], fill=ECYAN)
    else:
        ow = int(mrw * 0.88);  oh = int(5 + mouth_open * mrw * 0.62)
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)], fill=VISOR+(255,))
        draw.ellipse([(mcx-ow, mcy-oh), (mcx+ow, mcy+oh)], outline=ECYAN, width=4)
        if mouth_open > 0.28:
            tw = int(ow * 0.62)
            draw.arc([(mcx-tw, mcy-oh+3), (mcx+tw, mcy-oh//2+5)],
                     start=2, end=178, fill=(200, 215, 235, 200), width=3)

    # ── Hover glow (blurred on cropped layer for speed) ───────────────────────
    HW, HH = 440, 70
    hov = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))
    hd  = ImageDraw.Draw(hov)
    hp  = 0.55 + 0.45 * math.sin(t * math.pi * 2.2)
    for fx in (HW//2 - 92, HW//2 + 92):
        for ri in range(5):
            sr  = int((30 + ri*14) * hp)
            alp = max(6, int((90 - ri*16) * hp))
            hd.ellipse([fx-sr, HH//2-sr//6, fx+sr, HH//2+sr//6],
                       fill=(0, 188 + ri*10, 255, alp))
    hov = hov.filter(ImageFilter.GaussianBlur(radius=8))
    img.paste(hov, (cx - HW//2, RH - HH - 20), hov)

    # ── Whole-robot float offset ──────────────────────────────────────────────
    if bob != 0:
        final = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        final.paste(img, (0, bob), img)
        return final
    return img
