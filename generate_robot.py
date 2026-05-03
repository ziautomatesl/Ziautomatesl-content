from PIL import ImageDraw


def draw_robot(img, cx, cy, mouth=0.0, blink=0.0, glow=0.15, pose='neutral'):
    """
    Draw robot onto img (PIL RGBA).
    pose: 'neutral' | 'point_right' | 'point_left' | 'raise_right' | 'explain'
    """
    draw = ImageDraw.Draw(img)
    g = glow

    CYAN  = (0,  min(255, int(155 + 100*g)), min(255, int(195 + 60*g)))
    DCYAN = (0,  int(40  + 60*g),             int(75  + 60*g))
    BODY  = (12, 18, 35)
    PANEL = (22, 32, 58)
    METAL = (38, 52, 82)
    EDGE  = (0,  int(85  + 55*g), int(145 + 45*g))
    WHITE = (220, 235, 255)

    def rr(xy, r, fill, out=None, w=2):
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=out, width=w)

    def arm(x1, y1, x2, y2, w=28):
        """Draw an arm as a thick line (polygon) between two points."""
        import math
        dx, dy = x2 - x1, y2 - y1
        length = max(1, math.hypot(dx, dy))
        nx, ny = -dy / length * w, dx / length * w
        pts = [
            (x1 + nx, y1 + ny), (x1 - nx, y1 - ny),
            (x2 - nx, y2 - ny), (x2 + nx, y2 + ny),
        ]
        draw.polygon(pts, fill=PANEL, outline=EDGE)
        # Hand circle
        draw.ellipse([(x2-w+4, y2-w+4), (x2+w-4, y2+w-4)], fill=METAL, outline=EDGE, width=2)
        draw.ellipse([(x2-9,   y2-9),   (x2+9,   y2+9)],   fill=CYAN)

    # ── Antena ────────────────────────────────────────────────────────────────
    draw.line([(cx, cy-418), (cx, cy-362)], fill=EDGE, width=4)
    draw.ellipse([(cx-13, cy-440), (cx+13, cy-414)], fill=CYAN)
    draw.ellipse([(cx-6,  cy-433), (cx+6,  cy-421)], fill=WHITE)

    # ── Cabeza ────────────────────────────────────────────────────────────────
    ht, hb = cy - 360, cy - 162
    rr([(cx-150, ht), (cx+150, hb)], 34, PANEL, EDGE, 3)
    rr([(cx-84,  ht+10), (cx+84, ht+32)], 6, METAL, DCYAN, 1)

    # Ojos
    ey = ht + 98
    bh = max(2, int(22 * (1 - blink)))
    for ex in (cx - 72, cx + 72):
        draw.ellipse([(ex-32, ey-24), (ex+32, ey+24)], fill=DCYAN)
        draw.ellipse([(ex-24, ey-bh), (ex+24, ey+bh)],
                     fill=CYAN if blink < 0.9 else EDGE)
        if blink < 0.8:
            draw.ellipse([(ex-11, ey-11), (ex+11, ey+11)], fill=WHITE)

    # Boca
    my = ht + 163
    rr([(cx-74, my-23), (cx+74, my+27)], 10, BODY, DCYAN, 1)
    if mouth < 0.12:
        for i in range(5):
            xd = cx - 44 + i * 22
            draw.ellipse([(xd-5, my-5), (xd+5, my+5)], fill=CYAN)
    else:
        mw = int(53 + mouth * 15)
        mh = int(7  + mouth * 22)
        draw.ellipse([(cx-mw, my-mh), (cx+mw, my+mh)], fill=DCYAN)
        draw.ellipse([(cx-mw+7, my-mh+5), (cx+mw-7, my+mh-5)], fill=CYAN)

    # ── Cuello ────────────────────────────────────────────────────────────────
    rr([(cx-24, hb-6), (cx+24, hb+42)], 6, METAL, EDGE, 1)

    # ── Cuerpo ────────────────────────────────────────────────────────────────
    by1 = hb + 30
    by2 = by1 + 300
    rr([(cx-168, by1), (cx+168, by2)], 28, PANEL, EDGE, 3)
    rr([(cx-108, by1+26), (cx+108, by1+180)], 14, BODY, DCYAN, 1)

    # Núcleo
    ny = by1 + 94
    draw.ellipse([(cx-44, ny-44), (cx+44, ny+44)], fill=DCYAN)
    draw.ellipse([(cx-31, ny-31), (cx+31, ny+31)], fill=CYAN)
    draw.ellipse([(cx-14, ny-14), (cx+14, ny+14)], fill=WHITE)

    for i in range(4):
        ly = by1 + 33 + i * 22
        draw.line([(cx-97, ly), (cx-57, ly)], fill=EDGE, width=2)
        draw.line([(cx+57, ly), (cx+97, ly)], fill=EDGE, width=2)

    rr([(cx-76, by1+200), (cx+76, by1+264)], 8, BODY, DCYAN, 1)
    for i in range(3):
        xd = cx - 42 + i * 42
        draw.line([(xd, by1+210), (xd, by1+256)], fill=EDGE, width=1)

    # Hombros
    lshoulder = (cx - 198, by1 + 24)
    rshoulder = (cx + 198, by1 + 24)
    for sx, sy in (lshoulder, rshoulder):
        rr([(sx-38, sy-14), (sx+38, sy+54)], 22, METAL, EDGE, 2)
        draw.ellipse([(sx-10, sy+14), (sx+10, sy+34)], fill=CYAN)

    # ── Brazos según pose ─────────────────────────────────────────────────────
    lsx, lsy = cx - 198, by1 + 40
    rsx, rsy = cx + 198, by1 + 40

    if pose == 'neutral':
        arm(lsx, lsy, lsx - 14, lsy + 210)
        arm(rsx, rsy, rsx + 14, rsy + 210)

    elif pose == 'point_right':
        arm(lsx, lsy, lsx - 14, lsy + 210)
        arm(rsx, rsy, cx + 420, rsy - 20)   # brazo derecho apunta →

    elif pose == 'point_left':
        arm(lsx, lsy, cx - 420, lsy - 20)   # brazo izq apunta ←
        arm(rsx, rsy, rsx + 14, rsy + 210)

    elif pose == 'raise_right':
        arm(lsx, lsy, lsx - 14, lsy + 210)
        arm(rsx, rsy, cx + 280, by1 - 90)   # brazo derecho arriba ↗

    elif pose == 'explain':
        arm(lsx, lsy, cx - 300, by1 - 60)   # ambos brazos abiertos ↗↖
        arm(rsx, rsy, cx + 300, by1 - 60)

    # ── Cintura ───────────────────────────────────────────────────────────────
    rr([(cx-152, by2-10), (cx+152, by2+24)], 8, METAL, EDGE, 2)

    # ── Piernas ───────────────────────────────────────────────────────────────
    ly0 = by2 + 16
    for lx in (cx - 92, cx + 92):
        rr([(lx-43, ly0), (lx+43, ly0+165)], 16, PANEL, EDGE, 2)
        draw.line([(lx, ly0+28), (lx, ly0+136)], fill=EDGE, width=2)
        rr([(lx-49, ly0+154), (lx+53, ly0+200)], 14, METAL, EDGE, 2)
