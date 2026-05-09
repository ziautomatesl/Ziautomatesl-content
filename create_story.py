from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1080, 1920

CYAN   = (0,  229, 255)
BLUE   = (26, 107, 255)
PURPLE = (124, 58, 237)
WHITE  = (255, 255, 255)
BG     = (3,   1,  10)


def _font(size):
    for p in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _font_reg(size):
    for p in [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _background() -> Image.Image:
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # Two soft glow blobs
    blobs = [
        ((-200, -300, 900, 1000), (*PURPLE, 90)),
        ((300, 900, 1300, 2100), (*BLUE, 80)),
    ]
    for rect, color in blobs:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse(rect, fill=color)
        blurred = layer.filter(ImageFilter.GaussianBlur(radius=260))
        img = Image.alpha_composite(img, blurred)

    return img.convert("RGB")


def _gradient_line(draw, y):
    for x in range(W):
        t = x / W
        r = int(CYAN[0] * (1 - t) + BLUE[0] * t)
        g = int(CYAN[1] * (1 - t) + BLUE[1] * t)
        b = int(CYAN[2] * (1 - t) + BLUE[2] * t)
        alpha = int(180 * (1 - abs(2 * t - 1) ** 2))
        draw.point((x, y), fill=(r, g, b))


def _text_w(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _centered(draw, y, text, font, color):
    w, h = _text_w(draw, text, font)
    draw.text(((W - w) // 2, y), text, font=font, fill=color)
    return h


def _wrap(text, font, max_w, draw):
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] > max_w and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines


def _gradient_text(img, text, font, y, color_l, color_r):
    """Render text with horizontal gradient color."""
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bb = td.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2

    # Shadow
    td.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 140))
    # White text mask
    td.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Gradient color map
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for px in range(x, x + tw + 1):
        t = (px - x) / max(tw, 1)
        r = int(color_l[0] * (1 - t) + color_r[0] * t)
        g = int(color_l[1] * (1 - t) + color_r[1] * t)
        b = int(color_l[2] * (1 - t) + color_r[2] * t)
        gd.line([(px, y), (px, y + th)], fill=(r, g, b, 255))

    mask = tmp.split()[3]
    colored = Image.composite(grad, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    base = img.convert("RGBA")
    return Image.alpha_composite(base, colored).convert("RGB"), th


def create_story_image(content: dict, output: str = "zia_story.png") -> str:
    highlights = content.get("highlights", ["AUTOMATIZA"])
    script = content.get("script", "")

    main_text = highlights[0] if highlights else "AUTOMATIZA"
    sentences = [s.strip() for s in script.replace("\n", " ").split(".") if s.strip()]
    hook = sentences[0] if sentences else "Tu negocio en piloto automático"
    if len(hook) > 72:
        hook = hook[:70] + "…"

    # ── 1. Background ────────────────────────────────────────────
    img = _background()
    draw = ImageDraw.Draw(img)

    # ── 2. Brand badge (top, centered) ──────────────────────────
    badge_y = 160
    dot_r = 14
    dot_x, dot_y = W // 2 - 120, badge_y + dot_r
    for r in range(dot_r, 0, -1):
        t = 1 - r / dot_r
        col = tuple(int(CYAN[i] * (1 - t) + PURPLE[i] * t) for i in range(3))
        draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r], fill=col)
    draw.text((dot_x - 7, dot_y - 10), "Z", font=_font(22), fill=WHITE)

    draw.text((dot_x + dot_r + 16, badge_y), "ziautomate",
              font=_font_reg(44), fill=WHITE)

    # ── 3. Gradient divider ─────────────────────────────────────
    _gradient_line(draw, badge_y + 68)

    # ── 4. Main stat / highlight — big gradient text ─────────────
    parts = main_text.split()
    font_big = _font(182 if len(main_text) <= 6 else 128)
    stat_y = 380

    for part in parts:
        img, ph = _gradient_text(img, part, font_big, stat_y, CYAN, PURPLE)
        draw = ImageDraw.Draw(img)
        stat_y += ph + 20

    # ── 5. Hook sentence ─────────────────────────────────────────
    hook_y = stat_y + 80
    font_hook = _font_reg(54)
    max_w = W - 180
    lines = _wrap(hook, font_hook, max_w, draw)
    for line in lines[:3]:
        h = _centered(draw, hook_y, line, font_hook,
                      (200, 210, 230))
        hook_y += h + 18

    # ── 6. Bottom URL ────────────────────────────────────────────
    url_y = H - 200
    _gradient_line(draw, url_y - 40)
    font_url = _font(48)
    img, _ = _gradient_text(img, "ziautomate.netlify.app", font_url, url_y, CYAN, BLUE)

    img.save(output, "PNG")
    print(f"Historia generada: {output} ({W}x{H})")
    return output
