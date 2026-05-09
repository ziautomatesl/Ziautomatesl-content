import re
from PIL import Image, ImageDraw


# ── Extraer el dato más impactante del guion ──────────────────────────────────
def _extract_stat(script):
    patterns = [
        (r'(\d[\d\.]*)\s*euros?\s*(?:al\s*mes|semanales?)', "€{} / MES"),
        (r'(\d+)\s*%', "{}%"),
        (r'(\d+)\s*horas?\s*(?:al\s*mes|semanales?|cada\s*día)', "{} H AHORRADAS"),
        (r'(\d+)\s*horas?\s*al\s*día', "{} H / DÍA"),
        (r'(\d+)\s*minutos?\s*(?:por|en)\s*\w+', "{} MIN"),
        (r'(\d+)\s*clientes?\s*(?:al\s*mes|nuevos)', "{} CLIENTES / MES"),
        (r'(\d+)\s*leads?\s*(?:al\s*mes)?', "{} LEADS / MES"),
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, script, re.IGNORECASE)
        if m:
            num = m.group(1).replace('.', ',')
            return fmt.format(num)
    return None


# ── Elegir pasos del flujo según tema ─────────────────────────────────────────
def _flow_steps(topic, script):
    t = (topic + " " + script).lower()
    if 'whatsapp' in t and 'formulario' in t:
        return ["FORMULARIO", "WHATSAPP 30s", "CLIENTE LISTO"]
    if 'cita' in t or 'reserva' in t:
        return ["RESERVA ONLINE", "CONFIRMACIÓN", "RECORDATORIO"]
    if 'factura' in t:
        return ["PROYECTO", "FACTURA AUTO", "COBRO"]
    if 'email' in t and 'marketing' in t:
        return ["SUSCRIPCIÓN", "SECUENCIA IA", "VENTA AUTO"]
    if 'red' in t or 'instagram' in t or 'publicac' in t:
        return ["CONTENIDO IA", "PROGRAMADO", "PUBLICADO"]
    if 'lead' in t or 'captura' in t:
        return ["VISITA WEB", "CHAT IA", "LEAD TUYO"]
    if 'crm' in t:
        return ["CONTACTO", "CRM AUTO", "HISTORIAL"]
    if 'stock' in t or 'almacén' in t or 'tienda' in t:
        return ["VENTA", "STOCK SYNC", "SIN ERRORES"]
    if 'propuesta' in t:
        return ["DATOS CLIENTE", "PROPUESTA AUTO", "FIRMA DIGITAL"]
    return ["PROCESO MANUAL", "AUTOMATIZACIÓN", "TIEMPO LIBRE"]


# ── Icono del tema (dibujado con PIL) ─────────────────────────────────────────
def _draw_icon(draw, cx, cy, topic, script):
    t = (topic + " " + script).lower()
    CYAN = (0, 220, 255)
    DCYAN = (0, 70, 110)
    r = 28

    if 'whatsapp' in t or 'chat' in t or 'mensaje' in t:
        # Burbuja de chat
        draw.rounded_rectangle([(cx-r, cy-r+4), (cx+r, cy+r-4)],
                                radius=10, fill=DCYAN, outline=CYAN, width=2)
        draw.polygon([(cx-12, cy+r-4), (cx-22, cy+r+14), (cx+2, cy+r-4)],
                     fill=DCYAN, outline=CYAN)
    elif 'cita' in t or 'reserva' in t or 'calendar' in t:
        # Calendario
        draw.rounded_rectangle([(cx-r, cy-r), (cx+r, cy+r)],
                                radius=6, fill=DCYAN, outline=CYAN, width=2)
        draw.rectangle([(cx-r, cy-r), (cx+r, cy-r+14)], fill=CYAN)
        for row in range(2):
            for col in range(3):
                dx, dy = cx - 16 + col*16, cy - 4 + row*14
                draw.rectangle([(dx-4, dy-4), (dx+4, dy+4)], fill=CYAN)
    elif 'factura' in t or 'pago' in t or 'cobro' in t:
        # Documento
        draw.rounded_rectangle([(cx-r+4, cy-r), (cx+r-4, cy+r)],
                                radius=4, fill=DCYAN, outline=CYAN, width=2)
        for i in range(3):
            draw.line([(cx-14, cy-12+i*12), (cx+14, cy-12+i*12)],
                      fill=CYAN, width=2)
    elif 'email' in t or 'correo' in t:
        # Sobre
        draw.rounded_rectangle([(cx-r, cy-20), (cx+r, cy+20)],
                                radius=4, fill=DCYAN, outline=CYAN, width=2)
        draw.line([(cx-r, cy-20), (cx, cy+4), (cx+r, cy-20)],
                  fill=CYAN, width=2)
    else:
        # Rayo (default: automatización)
        draw.polygon([
            (cx+6, cy-r), (cx-4, cy-2), (cx+10, cy-2),
            (cx-6, cy+r), (cx+4, cy+2), (cx-10, cy+2)
        ], fill=CYAN)


# ── Función principal: dibuja la escena sobre un Image RGBA ───────────────────
def build_scene(topic, script, fonts, W, H):
    """
    Devuelve un Image RGBA con el panel informativo del tema.
    Se pega sobre el fondo, antes del robot.
    """
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    CYAN  = (0, 220, 255)
    DCYAN = (0, 70, 110)
    PANEL = (10, 18, 38, 210)
    EDGE  = (0, 100, 160)
    WHITE = (255, 255, 255)
    GREY  = (110, 125, 148)

    # ── Zona: y=165 → y=610 ──────────────────────────────────────────────────

    # Fondo semi-transparente del panel
    draw.rounded_rectangle([(60, 168), (W-60, 608)], radius=22,
                            fill=(8, 14, 30, 200), outline=(0, 60, 100, 200), width=2)

    # ── Icono + Tema ─────────────────────────────────────────────────────────
    _draw_icon(draw, 110, 230, topic, script)

    topic_short = topic.upper()
    if len(topic_short) > 32:
        topic_short = topic_short[:30] + "…"
    draw.text((148, 230), topic_short, fill=CYAN, font=fonts["sub"], anchor="lm")

    # Línea separadora
    draw.line([(90, 272), (W-90, 272)], fill=(0, 55, 90), width=2)

    # ── Dato clave ───────────────────────────────────────────────────────────
    stat = _extract_stat(script)
    if stat:
        # Caja destacada
        stat_y = 360
        draw.text((W//2, stat_y), stat, fill=WHITE, font=fonts["brand"], anchor="mm")
        # Barra decorativa bajo el número
        sw = min(len(stat) * 52, W - 200)
        draw.rectangle([(W//2-sw//2, stat_y+52), (W//2+sw//2, stat_y+56)], fill=CYAN)
        # Etiqueta
        draw.text((W//2, stat_y+76), "RESULTADO REAL",
                  fill=GREY, font=fonts["tag"], anchor="mm")
    else:
        draw.text((W//2, 360), "AUTOMATIZACIÓN INTELIGENTE",
                  fill=CYAN, font=fonts["cap"], anchor="mm")

    # ── Flujo de 3 pasos ─────────────────────────────────────────────────────
    steps = _flow_steps(topic, script)
    flow_y = 490
    box_w, box_h = 215, 62
    gap = 52
    total = len(steps) * box_w + (len(steps) - 1) * gap
    sx = W // 2 - total // 2

    for i, step in enumerate(steps):
        bx = sx + i * (box_w + gap)
        draw.rounded_rectangle([(bx, flow_y), (bx+box_w, flow_y+box_h)],
                                radius=12, fill=(12, 22, 45, 230), outline=EDGE, width=2)
        draw.text((bx + box_w//2, flow_y + box_h//2), step,
                  fill=WHITE, font=fonts["tag"], anchor="mm")
        if i < len(steps) - 1:
            ax = bx + box_w + 8
            draw.line([(ax, flow_y+box_h//2), (ax+gap-16, flow_y+box_h//2)],
                      fill=CYAN, width=3)
            draw.polygon([
                (ax+gap-16, flow_y+box_h//2-7),
                (ax+gap-16, flow_y+box_h//2+7),
                (ax+gap-4,  flow_y+box_h//2),
            ], fill=CYAN)

    return img
