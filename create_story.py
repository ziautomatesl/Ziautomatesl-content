from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, textwrap

W, H = 1080, 1920

# ── Brand colors ────────────────────────────────────────────────
BG      = (3,   1,  10)
CYAN    = (0,  229, 255)
BLUE    = (26, 107, 255)
PURPLE  = (124, 58, 237)
WHITE   = (255, 255, 255)
DIMWHITE= (200, 210, 230)
GRAY    = (100, 110, 130)

# ── Font loader ─────────────────────────────────────────────────
def _font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def _font_reg(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# ── Text helpers ────────────────────────────────────────────────
def _draw_text_centered(draw, y, text, font, color, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if shadow:
        for ox, oy in [(3,3),(4,4),(-2,2)]:
            draw.text((x+ox, y+oy), text, font=font, fill=(0,0,0,200))
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]

def _wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2] - bbox[0] > max_width and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines

def _draw_multiline_centered(draw, y, text, font, color, max_width, line_gap=14, shadow=True):
    lines = _wrap_text(text, font, max_width, draw)
    for line in lines:
        h = _draw_text_centered(draw, y, line, font, color, shadow=shadow)
        y += h + line_gap
    return y

# ── Rounded rectangle helper ────────────────────────────────────
def _rounded_rect(draw, xy, radius, fill, outline=None, outline_width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill,
                            outline=outline, width=outline_width)

# ── Aurora background ────────────────────────────────────────────
def _aurora_background():
    base = Image.new("RGBA", (W, H), (*BG, 255))
    blobs = [
        ((-150, -250,  820,  850), (*PURPLE, 110)),
        (( 400, 1050, 1380, 2150), (*BLUE,   100)),
        (( 180,  500,  900, 1350), (*CYAN,    55)),
        (( 700,  200, 1300,  900), (*BLUE,    60)),
    ]
    for rect, color in blobs:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse(rect, fill=color)
        blurred = layer.filter(ImageFilter.GaussianBlur(radius=220))
        base = Image.alpha_composite(base, blurred)

    # Subtle tech dot grid
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for gx in range(0, W, 72):
        for gy in range(0, H, 72):
            gd.ellipse([gx-1, gy-1, gx+1, gy+1], fill=(0, 229, 255, 12))
    base = Image.alpha_composite(base, grid)

    # Top and bottom vignette
    vign = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vign)
    for i in range(120):
        alpha = int(200 * (1 - i/120))
        vd.line([(0, i), (W, i)], fill=(0,0,0,alpha))
    for i in range(200):
        alpha = int(220 * (1 - i/200))
        vd.line([(0, H-1-i), (W, H-1-i)], fill=(0,0,0,alpha))
    base = Image.alpha_composite(base, vign)

    return base.convert("RGB")

# ── Gradient text via horizontal scan ────────────────────────────
def _gradient_text(img, draw, y, text, font, color_l, color_r, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (W - tw) // 2

    # render text on temp RGBA
    tmp = Image.new("RGBA", (W, H), (0,0,0,0))
    td  = ImageDraw.Draw(tmp)
    if shadow:
        td.text((x+4, y+4), text, font=font, fill=(0,0,0,160))
    td.text((x, y), text, font=font, fill=(255,255,255,255))

    # create horizontal gradient mask
    grad = Image.new("RGBA", (W, H), (0,0,0,0))
    gd   = ImageDraw.Draw(grad)
    for px in range(x, x+tw+1):
        t = (px - x) / max(tw, 1)
        r = int(color_l[0]*(1-t) + color_r[0]*t)
        g = int(color_l[1]*(1-t) + color_r[1]*t)
        b = int(color_l[2]*(1-t) + color_r[2]*t)
        gd.line([(px, y), (px, y+th)], fill=(r,g,b,255))

    # multiply text alpha by gradient color
    ta = tmp.split()[3]
    colored = Image.composite(grad, Image.new("RGBA",(W,H),(0,0,0,0)), ta)
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, colored)
    return result.convert("RGB")

# ── Progress bars ─────────────────────────────────────────────────
def _draw_progress_bars(draw, n=3, active=1):
    pad, gap, bar_h, top = 60, 10, 4, 52
    total_w = W - 2*pad
    bar_w   = (total_w - gap*(n-1)) // n
    for i in range(n):
        x0 = pad + i*(bar_w+gap)
        x1 = x0 + bar_w
        col = WHITE if i < active else (60, 65, 80)
        draw.rounded_rectangle([x0, top, x1, top+bar_h], radius=2, fill=col)
        if i == active:
            draw.rounded_rectangle([x0, top, x0+bar_w//2, top+bar_h], radius=2, fill=WHITE)

# ── Header: avatar + username ─────────────────────────────────────
def _draw_header(draw, fnt):
    av_x, av_y, av_r = 60, 72, 22
    # gradient circle avatar
    for r in range(av_r, 0, -1):
        t = 1 - r/av_r
        col = tuple(int(CYAN[i]*(1-t) + PURPLE[i]*t) for i in range(3))
        draw.ellipse([av_x-r, av_y-r, av_x+r, av_y+r], fill=col)
    draw.text((av_x-7, av_y-12), "Z", font=fnt, fill=WHITE)
    # username
    draw.text((av_x+av_r+14, av_y-12), "ziautomate", font=fnt, fill=WHITE)
    # time
    font_tiny = _font_reg(24)
    draw.text((av_x+av_r+14, av_y+10), "Ahora", font=font_tiny, fill=(*GRAY, 200))
    # close X
    draw.text((W-70, av_y-12), "✕", font=fnt, fill=(*GRAY,200))

# ── Stat highlight (big gradient text) ────────────────────────────
def _draw_stat_section(img, draw, highlight):
    font_xl = _font(148)
    font_lg  = _font(72)
    font_sub = _font_reg(38)

    parts = highlight.split()
    # find the "number" part (first token with digit)
    num_part  = next((p for p in parts if any(c.isdigit() or c in "€%+/-" for c in p)), parts[0])
    label_parts = [p for p in parts if p != num_part]
    label = " ".join(label_parts)

    # big number
    img = _gradient_text(img, draw, 240, num_part, font_xl, CYAN, BLUE, shadow=True)
    draw = ImageDraw.Draw(img)

    # label below
    if label:
        img = _gradient_text(img, draw, 420, label, font_lg, BLUE, PURPLE, shadow=True)
        draw = ImageDraw.Draw(img)

    return img, draw

# ── Divider ─────────────────────────────────────────────────────
def _draw_divider(img, y):
    div = Image.new("RGBA", (W, 3), (0,0,0,0))
    for px in range(W):
        t = px / W
        a = int(math.sin(t*math.pi)*60)
        r = int(CYAN[0]*(1-t) + PURPLE[0]*t)
        g = int(CYAN[1]*(1-t) + PURPLE[1]*t)
        b = int(CYAN[2]*(1-t) + PURPLE[2]*t)
        div.putpixel((px,0), (r,g,b,a))
        div.putpixel((px,1), (r,g,b,a//2))
    base = img.convert("RGBA")
    base.paste(div, (0, y), div)
    return base.convert("RGB")

# ── Hook sentence ─────────────────────────────────────────────────
def _draw_hook(img, draw, script):
    sentences = script.replace("¿", " ¿").split(".")
    hook = sentences[0].strip() + "." if sentences else script[:100]
    if len(hook) > 90:
        hook = hook[:88] + "..."
    font_hook = _font_reg(46)
    max_w = W - 140
    _draw_multiline_centered(draw, 660, hook, font_hook, DIMWHITE, max_w, line_gap=12)

# ── Question box ─────────────────────────────────────────────────
def _draw_question_box(img, draw, question):
    pad_x, pad_y = 70, 40
    box_x0 = 60
    box_x1 = W - 60
    box_y0 = 900

    # background card
    card = Image.new("RGBA", (W, H), (0,0,0,0))
    cd   = ImageDraw.Draw(card)
    cd.rounded_rectangle([box_x0, box_y0, box_x1, box_y0+240],
                          radius=28,
                          fill=(255,255,255,18),
                          outline=(*CYAN,40), width=1)
    base = img.convert("RGBA")
    img  = Image.alpha_composite(base, card).convert("RGB")
    draw = ImageDraw.Draw(img)

    # label
    font_label = _font(28)
    draw.text((box_x0+pad_x, box_y0+pad_y), "PREGUNTA DEL DÍA",
              font=font_label, fill=(*CYAN,180))

    # question text
    font_q = _font_reg(42)
    max_w  = box_x1 - box_x0 - pad_x*2
    lines  = _wrap_text(question, font_q, max_w, draw)
    qy = box_y0 + pad_y + 42
    for line in lines[:3]:
        draw.text((box_x0+pad_x, qy), line, font=font_q, fill=WHITE)
        qy += 52

    return img, ImageDraw.Draw(img)

# ── Answer pill buttons ───────────────────────────────────────────
def _draw_answer_pills(img, draw):
    pills = [
        ("SÍ, me pasa",      (*CYAN,  30), (*CYAN,  80)),
        ("Ya lo automaticé", (*BLUE,  30), (*BLUE,  80)),
    ]
    pill_y = 1180
    pill_h = 80
    pw = (W - 140 - 20) // 2
    for i, (label, bg, border) in enumerate(pills):
        px0 = 70 + i*(pw+20)
        px1 = px0 + pw
        card = Image.new("RGBA", (W, H), (0,0,0,0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([px0, pill_y, px1, pill_y+pill_h],
                              radius=40, fill=bg, outline=border, width=2)
        base = img.convert("RGBA")
        img  = Image.alpha_composite(base, card).convert("RGB")
        draw = ImageDraw.Draw(img)
        font_p = _font(36)
        bbox   = draw.textbbox((0,0), label, font=font_p)
        lw     = bbox[2]-bbox[0]
        lx     = px0 + (pw-lw)//2
        ly     = pill_y + (pill_h-28)//2
        draw.text((lx, ly), label, font=font_p, fill=WHITE)
    return img, ImageDraw.Draw(img)

# ── Link sticker ─────────────────────────────────────────────────
def _draw_link(img, draw):
    text  = "🔗  ziautomate.netlify.app"
    font  = _font_reg(38)
    bbox  = draw.textbbox((0,0), text, font=font)
    tw    = bbox[2]-bbox[0]
    pill_w = tw + 80
    px0   = (W - pill_w)//2
    px1   = px0 + pill_w
    py0, py1 = 1450, 1530

    card = Image.new("RGBA", (W, H), (0,0,0,0))
    cd   = ImageDraw.Draw(card)
    cd.rounded_rectangle([px0, py0, px1, py1], radius=40,
                          fill=(255,255,255,28), outline=(255,255,255,60), width=2)
    base = img.convert("RGBA")
    img  = Image.alpha_composite(base, card).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text(((W-tw)//2, py0+18), text, font=font, fill=WHITE)
    return img, ImageDraw.Draw(img)

# ── Brand watermark ────────────────────────────────────────────────
def _draw_brand(img, draw):
    font = _font(36)
    text = "ziautomate"
    bbox = draw.textbbox((0,0), text, font=font)
    tw   = bbox[2]-bbox[0]
    img  = _gradient_text(img, draw, H-130, text, font, CYAN, BLUE, shadow=False)
    return img, ImageDraw.Draw(img)

# ── Main public function ───────────────────────────────────────────
def create_story_image(content: dict, output: str = "zia_story.png") -> str:
    """
    Generates a 1080x1920 PNG story image from script content.
    Returns the path of the saved image.
    """
    highlight = content.get("highlights", ["AUTOMATIZA"])[0]
    script    = content.get("script", "")
    question  = content.get("engagement_question", "¿Qué automatizarías primero?")

    # 1. Background
    img  = _aurora_background()
    draw = ImageDraw.Draw(img)

    # 2. Progress bars
    _draw_progress_bars(draw, n=3, active=1)

    # 3. Header
    f_hdr = _font(34)
    _draw_header(draw, f_hdr)

    # 4. Big stat
    img, draw = _draw_stat_section(img, draw, highlight)

    # 5. Divider
    img  = _draw_divider(img, 610)
    draw = ImageDraw.Draw(img)

    # 6. Hook sentence
    _draw_hook(img, draw, script)

    # 7. Question box
    img, draw = _draw_question_box(img, draw, question)

    # 8. Answer pills
    img, draw = _draw_answer_pills(img, draw)

    # 9. Link sticker
    img, draw = _draw_link(img, draw)

    # 10. Brand watermark
    img, draw = _draw_brand(img, draw)

    img.save(output, "PNG")
    print(f"Historia generada: {output} ({W}x{H})")
    return output
