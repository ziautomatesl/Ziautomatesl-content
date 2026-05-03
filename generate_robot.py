import numpy as np
from PIL import Image, ImageDraw


def create_robot(w=800, h=900):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = w // 2

    BODY    = (12, 18, 35)
    PANEL   = (22, 32, 58)
    METAL   = (38, 52, 82)
    EDGE    = (0, 140, 190)
    CYAN    = (0, 220, 255)
    DCYAN   = (0, 70, 110)
    WHITE   = (220, 235, 255)

    def rr(xy, r, fill, outline=None, w=2):
        draw.rounded_rectangle(xy, radius=r, fill=fill,
                                outline=outline, width=w)

    # ── Antena ──────────────────────────────────────────────────────────
    draw.line([(cx, 30), (cx, 80)], fill=EDGE, width=4)
    draw.ellipse([(cx-12, 10), (cx+12, 34)], fill=CYAN)
    draw.ellipse([(cx-6, 16), (cx+6, 28)], fill=WHITE)

    # ── Cabeza ──────────────────────────────────────────────────────────
    hy1, hy2 = 75, 270
    rr([(cx-145, hy1), (cx+145, hy2)], 32, PANEL, EDGE, 3)
    # placa superior decorativa
    rr([(cx-80, hy1+10), (cx+80, hy1+30)], 6, METAL, DCYAN, 1)

    # Ojos
    for ex in [cx - 68, cx + 68]:
        draw.ellipse([(ex-30, 128), (ex+30, 188)], fill=DCYAN)  # halo
        draw.ellipse([(ex-22, 136), (ex+22, 180)], fill=CYAN)   # iris
        draw.ellipse([(ex-10, 148), (ex+10, 168)], fill=WHITE)  # brillo

    # Boca / pantalla
    rr([(cx-70, 205), (cx+70, 250)], 10, BODY, DCYAN, 1)
    for i in range(5):
        x = cx - 44 + i * 22
        draw.ellipse([(x-6, 220), (x+6, 236)], fill=CYAN)

    # ── Cuello ──────────────────────────────────────────────────────────
    rr([(cx-22, hy2-5), (cx+22, hy2+45)], 6, METAL, EDGE, 1)

    # ── Hombros ─────────────────────────────────────────────────────────
    by1 = hy2 + 35
    for sx, flip in [(cx - 200, -1), (cx + 200, 1)]:
        rr([(sx-38, by1-15), (sx+38, by1+55)], 22, METAL, EDGE, 2)
        draw.ellipse([(sx-10, by1+15), (sx+10, by1+35)], fill=CYAN)

    # ── Cuerpo ──────────────────────────────────────────────────────────
    by2 = by1 + 310
    rr([(cx-165, by1), (cx+165, by2)], 28, PANEL, EDGE, 3)

    # Panel pecho
    rr([(cx-105, by1+25), (cx+105, by1+185)], 14, BODY, DCYAN, 1)

    # Núcleo central (brilla)
    ny = by1 + 98
    draw.ellipse([(cx-42, ny-42), (cx+42, ny+42)], fill=DCYAN)
    draw.ellipse([(cx-30, ny-30), (cx+30, ny+30)], fill=CYAN)
    draw.ellipse([(cx-14, ny-14), (cx+14, ny+14)], fill=WHITE)

    # Líneas laterales del pecho
    for i in range(4):
        y = by1 + 35 + i * 20
        draw.line([(cx-95, y), (cx-55, y)], fill=EDGE, width=2)
        draw.line([(cx+55, y), (cx+95, y)], fill=EDGE, width=2)

    # Panel inferior cuerpo
    rr([(cx-75, by1+205), (cx+75, by1+270)], 8, BODY, DCYAN, 1)
    for i in range(3):
        x = cx - 40 + i * 40
        draw.line([(x, by1+215), (x, by1+260)], fill=EDGE, width=1)

    # ── Brazos ──────────────────────────────────────────────────────────
    for ax, flip in [(cx - 215, -1), (cx + 215, 1)]:
        rr([(ax-32, by1+50), (ax+32, by1+255)], 16, PANEL, EDGE, 2)
        rr([(ax-22, by1+60), (ax+22, by1+130)], 8, BODY, DCYAN, 1)
        # puño
        rr([(ax-28, by1+245), (ax+28, by1+290)], 12, METAL, EDGE, 2)
        draw.ellipse([(ax-8, by1+268), (ax+8, by1+285)], fill=CYAN)

    # ── Cintura ─────────────────────────────────────────────────────────
    rr([(cx-150, by2-10), (cx+150, by2+25)], 8, METAL, EDGE, 2)

    # ── Piernas ─────────────────────────────────────────────────────────
    legy = by2 + 18
    for lx in [cx - 90, cx + 90]:
        rr([(lx-42, legy), (lx+42, legy+175)], 16, PANEL, EDGE, 2)
        draw.line([(lx, legy+30), (lx, legy+140)], fill=EDGE, width=2)
        # pie
        rr([(lx-48, legy+160), (lx+52, legy+205)], 14, METAL, EDGE, 2)

    return img
