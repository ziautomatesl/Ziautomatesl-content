from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re

W, H = 1080, 1920

CYAN   = (0,  229, 255)
BLUE   = (26, 107, 255)
PURPLE = (124, 58, 237)
WHITE  = (255, 255, 255)
BG     = (3,   1,  10)

# Instagram safe zone (avoids story UI elements)
SAFE_TOP = 260
SAFE_BOT = 1660
MARGIN   = 70


def _font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _font_reg(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _background():
    img = Image.new("RGBA", (W, H), (*BG, 255))
    blobs = [
        ((-200, -300, 900, 1000), (*PURPLE, 85)),
        ((300,  900, 1300, 2100), (*BLUE,   75)),
    ]
    for rect, color in blobs:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse(rect, fill=color)
        blurred = layer.filter(ImageFilter.GaussianBlur(radius=260))
        img = Image.alpha_composite(img, blurred)
    return img.convert("RGB")


def _text_size(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def _centered_text(draw, y, text, font, color):
    tw, th = _text_size(draw, text, font)
    draw.text(((W - tw) // 2, y), text, font=font, fill=color)
    return th


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


def _gradient_text(img, text, font, y):
    """Render text with cyan→purple horizontal gradient."""
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td  = ImageDraw.Draw(tmp)
    bb  = td.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2

    td.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 120))
    td.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    for px in range(x, x + tw + 1):
        t = (px - x) / max(tw, 1)
        r = int(CYAN[0] * (1 - t) + PURPLE[0] * t)
        g = int(CYAN[1] * (1 - t) + PURPLE[1] * t)
        b = int(CYAN[2] * (1 - t) + PURPLE[2] * t)
        gd.line([(px, y), (px, y + th)], fill=(r, g, b, 255))

    mask    = tmp.split()[3]
    colored = Image.composite(grad, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    result  = Image.alpha_composite(img.convert("RGBA"), colored)
    return result.convert("RGB"), th


def _gradient_line(draw, y, alpha=160):
    for x in range(W):
        t = x / W
        r = int(CYAN[0] * (1 - t) + BLUE[0] * t)
        g = int(CYAN[1] * (1 - t) + BLUE[1] * t)
        b = int(CYAN[2] * (1 - t) + BLUE[2] * t)
        a = int(alpha * (1 - abs(2 * t - 1) ** 2))
        draw.point((x, y), fill=(r, g, b))
        if a > 20:
            draw.point((x, y + 1), fill=(r, g, b, a // 2))


def _fit_font_size(text, max_w, bold=True, min_size=60, max_size=160):
    """Return largest font size where text fits within max_w."""
    for size in range(max_size, min_size - 1, -4):
        f = _font(size) if bold else _font_reg(size)
        tmp = Image.new("RGB", (10, 10))
        d   = ImageDraw.Draw(tmp)
        bb  = d.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            return size
    return min_size


def create_story_image(content: dict, output: str = "zia_story.png") -> str:
    highlights = content.get("highlights", ["AUTOMATIZA"])
    script     = content.get("script", "")

    # Pick highlight — prefer a compact one (fits on screen better)
    main_text = min(highlights[:3], key=len) if highlights else "AUTOMATIZA"

    # Hook: first sentence of the script
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script) if s.strip()]
    hook = sentences[0] if sentences else "Tu negocio en piloto automático"
    if len(hook) > 80:
        hook = hook[:78] + "…"

    # Second supporting line (if available)
    support = sentences[1].strip() if len(sentences) > 1 else ""
    if len(support) > 75:
        support = support[:73] + "…"

    # ── Background ─────────────────────────────────────────────────
    img  = _background()
    draw = ImageDraw.Draw(img)

    # ── Brand badge (top of safe zone) ────────────────────────────
    badge_y = SAFE_TOP + 20
    dot_r, dot_x = 16, W // 2 - 130
    dot_cy = badge_y + dot_r
    for r in range(dot_r, 0, -1):
        t   = 1 - r / dot_r
        col = tuple(int(CYAN[i] * (1 - t) + PURPLE[i] * t) for i in range(3))
        draw.ellipse([dot_x - r, dot_cy - r, dot_x + r, dot_cy + r], fill=col)
    draw.text((dot_x - 8, dot_cy - 12), "Z", font=_font(24), fill=WHITE)
    draw.text((dot_x + dot_r + 18, badge_y + 4), "ziautomate",
              font=_font_reg(46), fill=(200, 210, 230))

    badge_bottom = badge_y + dot_r * 2 + 10

    # ── Thin gradient line ─────────────────────────────────────────
    line1_y = badge_bottom + 40
    _gradient_line(draw, line1_y)

    # ── Main stat / highlight — big gradient text ──────────────────
    max_text_w = W - MARGIN * 2
    words = main_text.split()

    if len(words) == 1:
        size = _fit_font_size(words[0], max_text_w, max_size=180)
    elif len(words) == 2:
        size = _fit_font_size(max(words, key=len), max_text_w, max_size=148)
    else:
        size = _fit_font_size(max(words, key=len), max_text_w, max_size=120)

    font_stat = _font(size)
    stat_y    = line1_y + 60

    for word in words:
        img, ph = _gradient_text(img, word, font_stat, stat_y)
        draw    = ImageDraw.Draw(img)
        stat_y += ph + 16

    stat_bottom = stat_y

    # ── Hook sentence ──────────────────────────────────────────────
    hook_y    = stat_bottom + 56
    font_hook = _font_reg(52)
    hook_lines = _wrap(hook, font_hook, max_text_w, draw)
    for line in hook_lines[:2]:
        h    = _centered_text(draw, hook_y, line, font_hook, (195, 208, 230))
        hook_y += h + 16

    # ── Supporting line (if present and space allows) ──────────────
    if support and hook_y + 80 < SAFE_BOT - 200:
        hook_y += 20
        font_sup = _font_reg(44)
        sup_lines = _wrap(support, font_sup, max_text_w - 80, draw)
        for line in sup_lines[:2]:
            h    = _centered_text(draw, hook_y, line, font_sup, (130, 145, 170))
            hook_y += h + 12

    content_bottom = hook_y + 20

    # ── Bottom: gradient line + URL ────────────────────────────────
    # Place URL at SAFE_BOT - 100, line 50px above
    url_y  = SAFE_BOT - 90
    line2_y = url_y - 50
    _gradient_line(draw, line2_y)

    font_url = _font(44)
    img, _   = _gradient_text(img, "ziautomate.netlify.app", font_url, url_y)

    img.save(output, "PNG")
    print(f"Historia generada: {output} ({W}x{H})")
    return output
