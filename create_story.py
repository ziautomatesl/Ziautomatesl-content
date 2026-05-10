from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, math

W, H = 1080, 1920

CYAN   = (0,  229, 255)
BLUE   = (26, 107, 255)
PURPLE = (124, 58, 237)
WHITE  = (255, 255, 255)
BG     = (3,   1,  10)

SAFE_TOP = 260
SAFE_BOT = 1650
MARGIN   = 72


# ── Fonts ────────────────────────────────────────────────────────────
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


# ── Background: rich aurora + vignette + diagonal lines ───────────────
def _background():
    img = Image.new("RGBA", (W, H), (*BG, 255))

    blobs = [
        # Purple sweep top-left
        ((-350, -450,  900, 1000), (*PURPLE, 105)),
        # Blue sweep bottom-right
        (( 350, 1100, 1550, 2400), (*BLUE,   100)),
        # Cyan spotlight center — the key visual focal point
        (( 100,  600,  980, 1480), (*CYAN,    70)),
        # Blue accent top-right
        (( 550, -250, 1350,  700), (*BLUE,    65)),
        # Purple accent bottom-left
        ((-250, 1350,  700, 2200), (*PURPLE,  75)),
    ]
    for rect, color in blobs:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(rect, fill=color)
        img = Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(230)))

    # Subtle diagonal tech lines
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    for y0 in range(-W, H + W, 68):
        ld.line([(0, y0), (W, y0 + W)], fill=(*CYAN, 9), width=1)
    img = Image.alpha_composite(img, lines)

    # Vignette: all 4 edges darken
    vign = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd   = ImageDraw.Draw(vign)
    for i in range(320):
        a = int(210 * (1 - i / 320) ** 2)
        vd.line([(0, i), (W, i)], fill=(0, 0, 0, a))
    for i in range(450):
        a = int(230 * (1 - i / 450) ** 2)
        vd.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, a))
    for i in range(160):
        a = int(120 * (1 - i / 160) ** 2)
        vd.line([(i, 0), (i, H)],         fill=(0, 0, 0, a))
        vd.line([(W - 1 - i, 0), (W - 1 - i, H)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, vign)

    return img.convert("RGB")


# ── Text helpers ──────────────────────────────────────────────────────
def _text_size(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


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


def _fit_font_size(text, max_w, max_size=170, min_size=60):
    for size in range(max_size, min_size - 1, -4):
        f   = _font(size)
        tmp = Image.new("RGB", (10, 10))
        d   = ImageDraw.Draw(tmp)
        bb  = d.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            return size
    return min_size


# ── Gradient text with glow ───────────────────────────────────────────
def _gradient_text_glow(img, text, font, y, color_l=CYAN, color_r=PURPLE, glow_r=28):
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td  = ImageDraw.Draw(tmp)
    bb  = td.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2

    # Glow layer (blurred cyan behind the text)
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow_layer).text((x, y), text, font=font, fill=(*CYAN, 160))
    img = Image.alpha_composite(img.convert("RGBA"),
                                 glow_layer.filter(ImageFilter.GaussianBlur(glow_r)))

    # Drop shadow
    td.text((x + 4, y + 5), text, font=font, fill=(0, 0, 0, 180))
    # White base for masking
    td.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Horizontal gradient
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    for px in range(x, x + tw + 1):
        t = (px - x) / max(tw, 1)
        r = int(color_l[0] * (1 - t) + color_r[0] * t)
        g = int(color_l[1] * (1 - t) + color_r[1] * t)
        b = int(color_l[2] * (1 - t) + color_r[2] * t)
        gd.line([(px, y), (px, y + th)], fill=(r, g, b, 255))

    mask    = tmp.split()[3]
    colored = Image.composite(grad, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask)
    img     = Image.alpha_composite(img, colored)

    return img.convert("RGB"), th


# ── Neon line ─────────────────────────────────────────────────────────
def _neon_line(img, y, width=W, alpha=200, color_l=CYAN, color_r=BLUE):
    line = Image.new("RGBA", (W, 4), (0, 0, 0, 0))
    ld   = ImageDraw.Draw(line)
    for x in range(width):
        t = x / max(width - 1, 1)
        r = int(color_l[0] * (1 - t) + color_r[0] * t)
        g = int(color_l[1] * (1 - t) + color_r[1] * t)
        b = int(color_l[2] * (1 - t) + color_r[2] * t)
        a = int(alpha * math.sin(t * math.pi))
        ld.line([(x, 1), (x, 2)], fill=(r, g, b, a))
        ld.line([(x, 0), (x, 0)], fill=(r, g, b, a // 3))
        ld.line([(x, 3), (x, 3)], fill=(r, g, b, a // 3))
    base = img.convert("RGBA")
    base.paste(line, (0, y), line)
    return base.convert("RGB")


# ── Glassmorphism card behind content ─────────────────────────────────
def _glass_card(img, y0, y1, x0=MARGIN - 20, x1=W - MARGIN + 20, radius=32):
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd   = ImageDraw.Draw(card)
    cd.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                          fill=(255, 255, 255, 14),
                          outline=(*CYAN, 30), width=1)
    # Inner glow edge
    cd.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=radius - 1,
                          fill=None, outline=(*BLUE, 15), width=1)
    return Image.alpha_composite(img.convert("RGBA"), card).convert("RGB")


# ── Brand header ──────────────────────────────────────────────────────
def _draw_brand_header(draw, y):
    """Small elegant brand badge: gradient dot + "ziautomate" """
    dot_r  = 14
    dot_cx = W // 2 - 118
    dot_cy = y + dot_r
    for r in range(dot_r, 0, -1):
        t   = 1 - r / dot_r
        col = tuple(int(CYAN[i] * (1 - t) + PURPLE[i] * t) for i in range(3))
        draw.ellipse([dot_cx - r, dot_cy - r, dot_cx + r, dot_cy + r], fill=col)
    draw.text((dot_cx - 7, dot_cy - 11), "Z", font=_font(22), fill=WHITE)
    draw.text((dot_cx + dot_r + 16, y + 3), "ziautomate",
              font=_font_reg(44), fill=(190, 205, 230))
    return dot_r * 2 + 10


# ── Main public function ───────────────────────────────────────────────
def create_story_image(content: dict, output: str = "zia_story.png") -> str:
    highlights = content.get("highlights", ["AUTOMATIZA"])
    script     = content.get("script", "")

    # Pick shortest highlight (fits better at large size)
    main_text = min(highlights[:4], key=len) if highlights else "AUTOMATIZA"

    # Sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script) if s.strip()]
    hook    = sentences[0][:80] if sentences else "Tu negocio en piloto automático"
    support = sentences[1][:72] if len(sentences) > 1 else ""

    # ── Build image ───────────────────────────────────────────────
    img  = _background()
    draw = ImageDraw.Draw(img)

    # ── Brand header ─────────────────────────────────────────────
    brand_h = _draw_brand_header(draw, SAFE_TOP + 18)
    top_after_brand = SAFE_TOP + 18 + brand_h + 44

    # ── Top neon line ─────────────────────────────────────────────
    img  = _neon_line(img, top_after_brand, color_l=CYAN, color_r=BLUE)
    draw = ImageDraw.Draw(img)

    # ── Stat text section ─────────────────────────────────────────
    stat_start = top_after_brand + 58
    words = main_text.split()
    max_w = W - MARGIN * 2

    size = _fit_font_size(max(words, key=len), max_w,
                           max_size=170 if len(words) == 1 else 140)
    font_stat = _font(size)

    stat_y = stat_start
    for word in words:
        img, ph = _gradient_text_glow(img, word, font_stat, stat_y,
                                       color_l=CYAN, color_r=PURPLE, glow_r=30)
        draw    = ImageDraw.Draw(img)
        stat_y += ph + 14

    stat_end = stat_y

    # ── Glassmorphism card behind hook text ───────────────────────
    hook_start = stat_end + 50
    font_hook  = _font_reg(50)
    hook_lines = _wrap(hook, font_hook, max_w, draw)

    sup_lines = []
    if support:
        font_sup = _font_reg(42)
        sup_lines = _wrap(support, font_sup, max_w - 60, draw)[:2]

    hook_total_h = (
        len(hook_lines[:2]) * 74 +
        (20 if sup_lines else 0) +
        len(sup_lines) * 62
    )
    card_y0 = hook_start - 30
    card_y1 = hook_start + hook_total_h + 30
    img  = _glass_card(img, card_y0, card_y1)
    draw = ImageDraw.Draw(img)

    # Draw hook
    hy = hook_start
    for line in hook_lines[:2]:
        tw, th = _text_size(draw, line, font_hook)
        draw.text(((W - tw) // 2, hy), line, font=font_hook, fill=(210, 220, 240))
        hy += th + 14

    # Draw support
    if sup_lines:
        hy += 14
        for line in sup_lines:
            tw, th = _text_size(draw, line, font_sup)
            draw.text(((W - tw) // 2, hy), line, font=font_sup, fill=(140, 155, 185))
            hy += th + 10

    content_end = hy + 20

    # ── Bottom neon line + URL ────────────────────────────────────
    url_y   = SAFE_BOT - 80
    line2_y = url_y - 54
    img     = _neon_line(img, line2_y, color_l=BLUE, color_r=PURPLE)

    font_url = _font(42)
    img, _   = _gradient_text_glow(img, "ziautomate.netlify.app",
                                    font_url, url_y, CYAN, BLUE, glow_r=18)

    img.save(output, "PNG")
    print(f"Historia generada: {output} ({W}x{H})")
    return output
