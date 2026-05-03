"""
Animates the real robot.png:
  - Black background → transparent (so Pexels image shows through)
  - Eyes glow brighter when speaking
  - Mouth opens/closes in sync with speech
  - Vertical bobbing effect
"""
import numpy as np
from PIL import Image, ImageDraw

ROBOT_W = 780   # width of robot in the video frame


def load_robot(path):
    """Load robot.png, remove black background, resize."""
    robot = Image.open(path).convert("RGBA")

    # Remove black/near-black background
    arr = np.array(robot)
    black = (arr[..., 0] < 20) & (arr[..., 1] < 20) & (arr[..., 2] < 22)
    arr[black, 3] = 0
    robot = Image.fromarray(arr)

    # Resize
    scale = ROBOT_W / robot.width
    new_h = int(robot.height * scale)
    robot = robot.resize((ROBOT_W, new_h), Image.LANCZOS)

    rw, rh = robot.width, robot.height

    # Sample face-visor background color (just above mouth, center)
    arr2 = np.array(robot)
    fy = int(rh * 0.30)
    fx = rw // 2
    fc = tuple(int(v) for v in arr2[fy, fx, :3])

    meta = {
        'w': rw, 'h': rh,
        # Mouth center — roughly 37% down the image, horizontally centered
        'mouth_cx': rw // 2,
        'mouth_cy': int(rh * 0.375),
        'mouth_rw': int(rw * 0.115),   # half-width of mouth area
        'mouth_rh': int(rh * 0.030),   # half-height when closed
        'face_bg':  fc,                 # color to cover original smile
    }
    return robot, meta


def robot_frame(robot_base, meta, mouth_open: float, glow: float, bob: int = 0):
    """
    Return an RGBA PIL Image of the animated robot.
    mouth_open : 0.0 = smile  →  1.0 = mouth fully open
    glow       : 0.0 = dim    →  1.0 = eyes blazing
    bob        : pixel offset (positive = down)
    """
    rw, rh = meta['w'], meta['h']

    # ── Apply vertical bob ────────────────────────────────────────────────────
    if bob != 0:
        canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
        canvas.paste(robot_base, (0, bob), robot_base)
        robot = canvas
    else:
        robot = robot_base.copy()

    # ── Eye glow via numpy ────────────────────────────────────────────────────
    arr = np.array(robot).astype(float)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # Detect cyan/teal eye pixels
    eye_mask = (r < 90) & (g > 110) & (b > 130) & (a > 80)

    arr[..., 0] = np.clip(r + eye_mask * glow * 75,  0, 255)
    arr[..., 1] = np.clip(g + eye_mask * glow * 55,  0, 255)
    arr[..., 2] = np.clip(b + eye_mask * glow * 25,  0, 255)

    robot = Image.fromarray(arr.astype(np.uint8), "RGBA")

    # ── Mouth animation ───────────────────────────────────────────────────────
    draw = ImageDraw.Draw(robot)
    cx  = meta['mouth_cx']
    cy  = meta['mouth_cy']
    mrw = meta['mouth_rw']
    mrh = meta['mouth_rh']
    fc  = meta['face_bg']

    g_val  = min(255, int(170 + 85 * glow))
    b_val  = min(255, int(210 + 45 * glow))
    CYAN   = (0, g_val, b_val, 255)
    DARK   = (fc[0], fc[1], fc[2], 255)

    # Cover the original smile
    cover_rw = int(mrw * 1.25)
    cover_rh = int(mrh * 3.5)
    draw.ellipse([(cx - cover_rw, cy - cover_rh),
                  (cx + cover_rw, cy + cover_rh)], fill=DARK)

    if mouth_open < 0.08:
        # Closed smile
        draw.arc([(cx - mrw, cy - mrw // 3),
                  (cx + mrw, cy + mrw // 3)],
                 start=8, end=172, fill=CYAN, width=5)
    else:
        # Open mouth — oval that grows with mouth_open
        ow = int(mrw * 0.92)
        oh = int(mrh * 0.6 + mouth_open * mrw * 0.55)
        # Dark interior
        draw.ellipse([(cx - ow, cy - oh), (cx + ow, cy + oh)],
                     fill=(max(0, fc[0]-4), max(0, fc[1]-4), max(0, fc[2]-4), 255))
        # Cyan rim
        draw.ellipse([(cx - ow, cy - oh), (cx + ow, cy + oh)],
                     outline=CYAN, width=4)
        # Upper lip hint (white teeth)
        if mouth_open > 0.25:
            tw = int(ow * 0.7)
            draw.arc([(cx - tw, cy - oh + 3), (cx + tw, cy - oh // 2)],
                     start=0, end=180, fill=(210, 225, 240, 200), width=3)

    return robot
