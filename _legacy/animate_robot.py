"""
2.5D parallax animation of the real robot.png.
- Black background removed with feathered edges
- Robot split into layers (body, head, arm) animated independently
- Mouth region overlay for lip sync
- Eye glow via numpy
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Target width for robot in the video frame
TARGET_W = 860


def _remove_bg(img: Image.Image) -> Image.Image:
    """Remove pure-black background with feathered edges."""
    img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32)

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    # Luminance of each pixel
    lum = 0.299*r + 0.587*g + 0.114*b

    # Alpha: fully transparent for dark pixels, fully opaque for bright ones
    # Smooth ramp between 8 and 40 luminance
    alpha = np.clip((lum - 8) / 32.0 * 255, 0, 255)

    # Feather the edges by blurring the alpha
    alpha_img = Image.fromarray(alpha.astype(np.uint8), 'L')
    alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(radius=1.2))
    alpha_clean = np.array(alpha_img).astype(np.float32)

    arr[..., 3] = np.clip(alpha_clean, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def load_robot(path: str):
    """
    Load robot.png, remove bg, resize, and return (base_img, meta).
    meta contains proportional coordinates for face/mouth/eyes.
    """
    raw = Image.open(path).convert("RGB")
    scale = TARGET_W / raw.width
    new_h = int(raw.height * scale)
    raw = raw.resize((TARGET_W, new_h), Image.LANCZOS)

    robot = _remove_bg(raw)
    rw, rh = robot.width, robot.height

    # Approximate regions based on visual analysis of the robot
    meta = {
        'w': rw, 'h': rh,
        # Head bounding box (proportional)
        'head_x1': int(rw * 0.18), 'head_y1': 0,
        'head_x2': int(rw * 0.82), 'head_y2': int(rh * 0.43),
        # Body region
        'body_y1': int(rh * 0.37), 'body_y2': rh,
        # Right arm (raised) region
        'arm_x1': int(rw * 0.55), 'arm_y1': int(rh * 0.22),
        'arm_x2': rw,              'arm_y2': int(rh * 0.58),
        # Mouth center (proportional within image)
        'mouth_cx': int(rw * 0.50),
        'mouth_cy': int(rh * 0.375),
        'mouth_rw': int(rw * 0.105),
        'mouth_rh': int(rh * 0.028),
        # Eye positions
        'eye_lx': int(rw * 0.385), 'eye_rx': int(rw * 0.615),
        'eye_y':  int(rh * 0.295),
        'eye_rw': int(rw * 0.068), 'eye_rh': int(rh * 0.038),
    }
    return robot, meta


def _glow_eyes(robot: Image.Image, meta: dict, glow: float) -> Image.Image:
    """Boost cyan eye pixels based on glow level."""
    arr = np.array(robot).astype(np.float32)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # Detect cyan/teal eye pixels in the eye region
    ey1 = meta['eye_y'] - meta['eye_rh'] - 10
    ey2 = meta['eye_y'] + meta['eye_rh'] + 10
    mask = np.zeros(arr.shape[:2], bool)
    mask[ey1:ey2, :] = (r[ey1:ey2, :] < 100) & \
                       (g[ey1:ey2, :] > 100) & \
                       (b[ey1:ey2, :] > 130) & \
                       (a[ey1:ey2, :] > 60)

    arr[..., 0] = np.clip(r + mask * glow * 80,  0, 255)
    arr[..., 1] = np.clip(g + mask * glow * 60,  0, 255)
    arr[..., 2] = np.clip(b + mask * glow * 25,  0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def _draw_mouth(robot: Image.Image, meta: dict, mouth_open: float, glow: float):
    """Overlay animated mouth on robot image (modifies in place)."""
    draw = ImageDraw.Draw(robot)
    cx  = meta['mouth_cx']
    cy  = meta['mouth_cy']
    mrw = meta['mouth_rw']
    mrh = meta['mouth_rh']

    gv = min(255, int(168 + 87 * glow))
    bv = min(255, int(210 + 45 * glow))
    CYAN  = (0, gv, bv, 255)

    # Sample the face visor color at the mouth region to use as cover
    arr = np.array(robot)
    # Sample above the mouth (should be the dark visor)
    sample_y = max(0, cy - mrh - 4)
    fc_pixel  = arr[sample_y, cx]
    DARK = (int(fc_pixel[0]), int(fc_pixel[1]), int(fc_pixel[2]), 255)

    # Cover original smile
    draw.ellipse([(cx - mrw - 8, cy - mrh*3 - 2),
                  (cx + mrw + 8, cy + mrh*3 + 2)], fill=DARK)

    if mouth_open < 0.07:
        # Closed smile
        draw.arc([(cx - mrw, cy - mrw//3),
                  (cx + mrw, cy + mrw//3)],
                 start=8, end=172, fill=CYAN, width=5)
        draw.ellipse([(cx-mrw-2, cy-4), (cx-mrw+7, cy+5)], fill=CYAN)
        draw.ellipse([(cx+mrw-7, cy-4), (cx+mrw+2, cy+5)], fill=CYAN)
    else:
        ow = int(mrw * 0.90)
        oh = int(4 + mouth_open * mrw * 0.60)
        draw.ellipse([(cx-ow, cy-oh), (cx+ow, cy+oh)], fill=DARK)
        draw.ellipse([(cx-ow, cy-oh), (cx+ow, cy+oh)], outline=CYAN, width=4)
        if mouth_open > 0.28:
            tw = int(ow * 0.62)
            draw.arc([(cx-tw, cy-oh+3), (cx+tw, cy-oh//2+5)],
                     start=2, end=178, fill=(200, 215, 235, 200), width=3)


def make_frame(robot_base: Image.Image, meta: dict,
               t: float, mouth_open: float, glow: float) -> Image.Image:
    """
    Compose an animated robot frame.
    Returns RGBA image of size (TARGET_W, meta['h']).
    """
    rw, rh = meta['w'], meta['h']

    # ── Layer animation parameters ────────────────────────────────────────────
    # Body: gentle breathing scale + slow sway
    body_scale  = 1.0 + 0.012 * math.sin(t * math.pi * 1.4)
    body_sway   = int(3  * math.sin(t * math.pi * 0.9))
    body_bob    = int(5  * math.sin(t * math.pi * 1.4))

    # Head: more movement — bobs more, subtle turn (horizontal stretch)
    head_bob    = int(9  * math.sin(t * math.pi * 1.4 + 0.3))
    head_turn   = 0.04  * math.sin(t * math.pi * 0.8)   # horizontal stretch factor

    # Raised arm: oscillates up/down
    arm_swing   = int(12 * math.sin(t * math.pi * 1.8 + 0.8))

    # ── Canvas ────────────────────────────────────────────────────────────────
    canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))

    # ── BODY LAYER ───────────────────────────────────────────────────────────
    by1 = meta['body_y1']
    body_region = robot_base.crop((0, by1, rw, rh))
    # Scale
    bw = int(rw * body_scale)
    bh = int((rh - by1) * body_scale)
    if bw > 0 and bh > 0:
        body_scaled = body_region.resize((bw, bh), Image.LANCZOS)
        bx = (rw - bw) // 2 + body_sway
        by = by1 + body_bob + (rh - by1 - bh) // 2
        canvas.paste(body_scaled, (bx, by), body_scaled)

    # ── HEAD LAYER ────────────────────────────────────────────────────────────
    hx1, hy1 = meta['head_x1'], meta['head_y1']
    hx2, hy2 = meta['head_x2'], meta['head_y2']
    head_region = robot_base.crop((hx1, hy1, hx2, hy2))
    hw = hx2 - hx1
    hh = hy2 - hy1

    # Subtle horizontal perspective warp (simulate turn)
    turn_px = int(hw * abs(head_turn))
    if head_turn > 0:
        # Turn right: squeeze left side
        head_w = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
        head_warp = head_region.transform(
            (hw, hh), Image.AFFINE,
            (1 + head_turn * 0.4, head_turn * 0.1, -turn_px * 0.5,
             0, 1, 0), resample=Image.BILINEAR)
        head_w.paste(head_warp, (0, 0), head_warp)
        head_region = head_w
    elif head_turn < 0:
        head_w = Image.new("RGBA", (hw, hh), (0, 0, 0, 0))
        head_warp = head_region.transform(
            (hw, hh), Image.AFFINE,
            (1 + head_turn * 0.4, head_turn * 0.1, turn_px * 0.5,
             0, 1, 0), resample=Image.BILINEAR)
        head_w.paste(head_warp, (0, 0), head_warp)
        head_region = head_w

    canvas.paste(head_region,
                 (hx1 + body_sway // 2, hy1 + head_bob), head_region)

    # ── RAISED ARM LAYER (right arm) ─────────────────────────────────────────
    ax1, ay1 = meta['arm_x1'], meta['arm_y1']
    ax2, ay2 = meta['arm_x2'], meta['arm_y2']
    arm_region = robot_base.crop((ax1, ay1, ax2, ay2))
    canvas.paste(arm_region,
                 (ax1 + body_sway, ay1 + arm_swing), arm_region)

    # ── Eye glow + mouth animation ────────────────────────────────────────────
    canvas = _glow_eyes(canvas, meta, glow)
    _draw_mouth(canvas, meta, mouth_open, glow)

    return canvas
