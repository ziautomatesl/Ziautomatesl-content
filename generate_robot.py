from PIL import ImageDraw


def draw_robot(img, cx, cy, mouth=0.0, blink=0.0, glow=0.15):
    """
    Dibuja el robot sobre img (PIL RGBA) centrado en (cx, cy).
    mouth : 0.0 cerrada  → 1.0 abierta
    blink : 0.0 ojos abiertos → 1.0 cerrados
    glow  : 0.0 apagado  → 1.0 máximo brillo cyan
    """
    draw = ImageDraw.Draw(img)

    g = glow
    CYAN  = (0,  min(255, int(160 + 95*g)),  min(255, int(200 + 55*g)))
    DCYAN = (0,  int(45 + 55*g),              int(80 + 55*g))
    BODY  = (12, 18,  35)
    PANEL = (22, 32,  58)
    METAL = (38, 52,  82)
    EDGE  = (0,  int(90 + 50*g), int(150 + 40*g))
    WHITE = (220, 235, 255)

    def rr(xy, r, fill, out=None, w=2):
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=out, width=w)

    # ── Antena ────────────────────────────────────────────────────────
    draw.line([(cx, cy-415), (cx, cy-360)], fill=EDGE, width=4)
    draw.ellipse([(cx-13, cy-437), (cx+13, cy-411)], fill=CYAN)
    draw.ellipse([(cx-6,  cy-430), (cx+6,  cy-418)], fill=WHITE)

    # ── Cabeza ────────────────────────────────────────────────────────
    ht = cy - 358
    hb = cy - 165
    rr([(cx-148, ht), (cx+148, hb)], 34, PANEL, EDGE, 3)
    rr([(cx-82,  ht+10), (cx+82, ht+32)], 6, METAL, DCYAN, 1)

    # Ojos
    ey = ht + 97
    bh = max(2, int(22 * (1 - blink)))
    for ex in (cx - 70, cx + 70):
        draw.ellipse([(ex-31, ey-23), (ex+31, ey+23)], fill=DCYAN)
        draw.ellipse([(ex-23, ey-bh), (ex+23, ey+bh)], fill=CYAN if blink < 0.9 else EDGE)
        if blink < 0.8:
            draw.ellipse([(ex-11, ey-10), (ex+11, ey+10)], fill=WHITE)

    # Boca
    my = ht + 162
    rr([(cx-72, my-22), (cx+72, my+26)], 10, BODY, DCYAN, 1)
    if mouth < 0.12:
        for i in range(5):
            xd = cx - 44 + i * 22
            draw.ellipse([(xd-5, my-5), (xd+5, my+5)], fill=CYAN)
    else:
        mw = int(52 + mouth * 14)
        mh = int(6  + mouth * 20)
        draw.ellipse([(cx-mw, my-mh), (cx+mw, my+mh)], fill=DCYAN)
        draw.ellipse([(cx-mw+7, my-mh+5), (cx+mw-7, my+mh-5)], fill=CYAN)

    # ── Cuello ────────────────────────────────────────────────────────
    rr([(cx-23, hb-6), (cx+23, hb+42)], 6, METAL, EDGE, 1)

    # ── Cuerpo ────────────────────────────────────────────────────────
    by1 = hb + 30
    by2 = by1 + 298
    rr([(cx-168, by1), (cx+168, by2)], 28, PANEL, EDGE, 3)
    rr([(cx-108, by1+26), (cx+108, by1+178)], 14, BODY, DCYAN, 1)

    # Núcleo
    ny = by1 + 92
    draw.ellipse([(cx-44, ny-44), (cx+44, ny+44)], fill=DCYAN)
    draw.ellipse([(cx-31, ny-31), (cx+31, ny+31)], fill=CYAN)
    draw.ellipse([(cx-14, ny-14), (cx+14, ny+14)], fill=WHITE)

    for i in range(4):
        ly = by1 + 32 + i * 22
        draw.line([(cx-97, ly), (cx-57, ly)], fill=EDGE, width=2)
        draw.line([(cx+57, ly), (cx+97, ly)], fill=EDGE, width=2)

    rr([(cx-76, by1+198), (cx+76, by1+262)], 8, BODY, DCYAN, 1)
    for i in range(3):
        xd = cx - 42 + i * 42
        draw.line([(xd, by1+208), (xd, by1+254)], fill=EDGE, width=1)

    # Hombros
    for sx in (cx - 200, cx + 200):
        rr([(sx-38, by1-16), (sx+38, by1+56)], 22, METAL, EDGE, 2)
        draw.ellipse([(sx-10, by1+16), (sx+10, by1+36)], fill=CYAN)

    # Brazos
    for ax in (cx - 217, cx + 217):
        rr([(ax-33, by1+50), (ax+33, by1+252)], 16, PANEL, EDGE, 2)
        rr([(ax-23, by1+62), (ax+23, by1+132)], 8,  BODY, DCYAN, 1)
        rr([(ax-29, by1+242), (ax+29, by1+288)], 12, METAL, EDGE, 2)
        draw.ellipse([(ax-9, by1+262), (ax+9, by1+280)], fill=CYAN)

    # Cintura
    rr([(cx-152, by2-10), (cx+152, by2+24)], 8, METAL, EDGE, 2)

    # Piernas
    ly0 = by2 + 16
    for lx in (cx - 92, cx + 92):
        rr([(lx-43, ly0), (lx+43, ly0+162)], 16, PANEL, EDGE, 2)
        draw.line([(lx, ly0+28), (lx, ly0+132)], fill=EDGE, width=2)
        rr([(lx-49, ly0+152), (lx+53, ly0+196)], 14, METAL, EDGE, 2)
