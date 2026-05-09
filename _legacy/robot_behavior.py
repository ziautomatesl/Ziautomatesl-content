"""
ZIA behavior engine.

Converts word_timings into a sorted event timeline with:
  - Intent detection per phrase (explain / emphasize / positive / question / reveal / closing)
  - Micro-delay layering: eyes first → gesture 300 ms later → energy surge
  - Special reveal sequence: freeze → look-away → burst
  - Smooth interpolation between events (gaze, energy)

Public API:
    build_timeline(word_timings, script_text='') → list[event]
    get_behavior(t, events)                     → dict
"""

# ── Intent keyword bank (Spanish) ────────────────────────────────────────────
_KEYWORDS = {
    'positive':  ['ahorra', 'gana', '€', 'euro', 'beneficio', 'fácil', 'mejor',
                  'gratis', 'rápido', 'automático', 'ventaja', 'sencillo', 'genial'],
    'emphasize': ['importante', 'clave', 'fundamental', 'definitivamente', 'siempre',
                  'todos', 'cada', 'nunca', '100', 'exactamente', 'imprescindible'],
    'explain':   ['porque', 'significa', 'funciona', 'básicamente', 'consiste',
                  'permite', 'mediante', 'así', 'ejemplo', 'proceso', 'cuando'],
    'question':  ['qué', 'cómo', 'cuánto', 'por qué', 'cuándo', 'dónde', '?', '¿'],
    'reveal':    ['imagina', 'pero', 'ahora', 'resulta', 'descubre', 'secreto',
                  'realidad', 'verdad', 'increíble', 'sorprendente', 'sin embargo'],
    'closing':   ['gracias', 'suscríbete', 'síguenos', 'comenta', 'comparte',
                  'recuerda', 'hasta', 'nos vemos', 'dale', 'like'],
}

# intent → (pose, gaze_x, gaze_y, energy)
_PROFILE = {
    'positive':  ('thumbsup',  0.00,  0.00, 1.20),
    'emphasize': ('point_cam', 0.00,  0.00, 1.40),
    'explain':   ('explain',   0.22, -0.20, 1.00),
    'question':  ('shrug',     0.00, -0.55, 0.90),
    'reveal':    ('explain',   0.00,  0.00, 1.60),
    'closing':   ('wave',      0.00,  0.00, 1.10),
    'talking':   ('neutral',   0.00,  0.00, 1.00),
}


def _detect_intent(words, position_frac):
    if position_frac > 0.84:
        return 'closing'
    text = ' '.join(words).lower()
    for intent, kws in _KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return intent
    return 'talking'


def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


# ── Public API ────────────────────────────────────────────────────────────────

def build_timeline(word_timings, script_text=''):
    """
    Build a sorted list of behavior events from word_timings.
    Each event: {t, pose, gaze_x, gaze_y, energy}
    """
    if not word_timings:
        return [{'t': 0.0, 'pose': 'neutral',
                 'gaze_x': 0.0, 'gaze_y': 0.0, 'energy': 1.0}]

    total = len(word_timings)

    # ── Group words into phrases ──────────────────────────────────────────────
    phrases, group = [], [word_timings[0]]
    for i in range(1, total):
        gap          = word_timings[i]['start'] - word_timings[i-1]['end']
        ends_sent    = any(p in word_timings[i-1].get('word', '')
                           for p in ('.', '!', '?'))
        if gap > 0.38 or ends_sent:
            phrases.append(group)
            group = []
        group.append(word_timings[i])
    if group:
        phrases.append(group)

    # ── Build events ──────────────────────────────────────────────────────────
    events     = []
    word_count = 0

    for phrase in phrases:
        t0     = phrase[0]['start']
        words  = [w['word'] for w in phrase]
        frac   = (word_count + len(phrase) // 2) / max(total, 1)
        intent = _detect_intent(words, frac)
        word_count += len(phrase)

        pose, gx, gy, energy = _PROFILE.get(intent, _PROFILE['talking'])

        # Layer 1 – Eyes shift immediately (body stays still)
        events.append({'t': t0,
                       'pose': 'neutral', 'gaze_x': gx, 'gaze_y': gy,
                       'energy': 0.52})

        if intent == 'reveal':
            # Dramatic sequence: freeze → look away → burst
            events.append({'t': t0 + 0.18,
                           'pose': 'neutral', 'gaze_x': -0.30, 'gaze_y': -0.25,
                           'energy': 0.28})
            events.append({'t': t0 + 0.55,
                           'pose': pose, 'gaze_x': 0.00, 'gaze_y': 0.00,
                           'energy': 1.68})
        else:
            # Layer 2 – Gesture fires 300 ms after phrase starts
            events.append({'t': t0 + 0.30,
                           'pose': pose, 'gaze_x': gx, 'gaze_y': gy,
                           'energy': energy})

    events.sort(key=lambda e: e['t'])
    return events


def get_behavior(t, events):
    """
    Return interpolated behavior dict at time t.
    Pose switches at event time; gaze and energy are smoothly interpolated.
    """
    if not events:
        return {'pose': 'neutral', 'gaze_x': 0.0, 'gaze_y': 0.0, 'energy': 1.0}

    prev = events[0]
    nxt  = None
    for ev in events:
        if ev['t'] <= t:
            prev = ev
        else:
            nxt = ev
            break

    if nxt is None:
        return prev

    span = max(0.001, nxt['t'] - prev['t'])
    f    = _smoothstep(min(1.0, (t - prev['t']) / min(span, 0.32)))

    return {
        'pose':   prev['pose'] if f < 0.50 else nxt['pose'],
        'gaze_x': prev['gaze_x'] + (nxt['gaze_x'] - prev['gaze_x']) * f,
        'gaze_y': prev['gaze_y'] + (nxt['gaze_y'] - prev['gaze_y']) * f,
        'energy': prev['energy'] + (nxt['energy'] - prev['energy']) * f,
    }
