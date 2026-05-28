import React from "react";
import {
  AbsoluteFill, interpolate, useCurrentFrame, Easing, Img, staticFile,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Montserrat";

const { fontFamily: MONT } = loadFont("normal", { weights: ["400", "600", "700", "900"], subsets: ["latin"] });

// ── Brand ─────────────────────────────────────────────────────────────────────
const CYAN   = "#00d4ff";
const BLUE   = "#1830ff";
const WHITE  = "#ffffff";
const WDIM   = "rgba(255,255,255,0.75)";
const WFAINT = "rgba(255,255,255,0.45)";
const BG     = "#060610";

// ── Layout ────────────────────────────────────────────────────────────────────
const SL = 54, SR = 936, ST = 145;
const SLIDE = 140, TRANS = 25;
// 6 slides × 140 – 5 transitions × 25 = 715 total frames

export interface ZiaCarouselProps {
  topic:           string;   // main headline (split into 2 lines)
  tag:             string;   // small uppercase label (e.g. "Automatización IA")
  stat_number:     number;   // big animated number (e.g. 78)
  stat_suffix:     string;   // e.g. "%" or "x"
  stat_context:    string;   // what it means (e.g. "van al negocio que responde primero")
  stat_footnote:   string;   // small note (e.g. "Y sin respuesta, se van a tu competencia.")
  solution_line1:  string;   // e.g. "Una IA que"
  solution_line2:  string;   // gradient (e.g. "responde al instante.")
  solution_word1:  string;   // single word (e.g. "Califica.")
  solution_word2:  string;   // single word (e.g. "Agenda.")
  solution_sub:    string;   // small text
  vision_hook:     string;   // e.g. "Te despiertas."
  vision_result:   string;   // gradient (e.g. "3 citas agendadas.")
  vision_body:     string;   // e.g. "Tu negocio trabajó toda la noche mientras dormías."
  vision_brand:    string;   // e.g. "Eso es ziautomate."
  bullet1:         string;
  bullet2:         string;
  bullet3:         string;
  cta_sub:         string;   // e.g. "Sin empleados extra. Sin estrés. Sin límites."
  cta_button:      string;   // e.g. "Activa tu negocio 24/7"
}

export const defaultZiaCarouselProps: ZiaCarouselProps = {
  topic:          "Tu negocio abierto las 24 horas.",
  tag:            "Automatización IA",
  stat_number:    78,
  stat_suffix:    "%",
  stat_context:   "de las ventas va al negocio que responde primero.",
  stat_footnote:  "No al mejor. Al más rápido.",
  solution_line1: "Una IA que",
  solution_line2: "responde al instante.",
  solution_word1: "Califica.",
  solution_word2: "Agenda.",
  solution_sub:   "A las 3am si hace falta.",
  vision_hook:    "Te despiertas.",
  vision_result:  "3 citas agendadas.",
  vision_body:    "Tu negocio trabajó toda la noche mientras dormías.",
  vision_brand:   "Eso es ziautomate.",
  bullet1:        "Clientes atendidos a las 2am. Cita cerrada.",
  bullet2:        "Lista de espera llena en 48h. Sin llamadas.",
  bullet3:        "+30% de conversión. Mismo presupuesto.",
  cta_sub:        "Sin empleados extra. Sin estrés. Sin límites.",
  cta_button:     "Activa tu negocio 24/7",
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const GradText: React.FC<{ children: React.ReactNode; size: number; spacing?: string }> = ({ children, size, spacing }) => (
  <div style={{
    fontFamily: MONT, fontWeight: 900, fontSize: size, lineHeight: 0.95,
    letterSpacing: spacing ?? "-2px",
    background: `linear-gradient(90deg,${CYAN},${BLUE})`,
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
  }}>{children}</div>
);

const Logo: React.FC = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
    <div style={{ width: 10, height: 10, borderRadius: "50%", background: `linear-gradient(135deg,${CYAN},${BLUE})` }} />
    <span style={{
      fontFamily: MONT, fontWeight: 800, fontSize: 22, letterSpacing: 1,
      background: `linear-gradient(90deg,${CYAN},${BLUE})`,
      WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
    }}>ziautomate</span>
  </div>
);

// mk(frame, startFrame) → {op, y}
const mkAnim = (f: number, s: number) => ({
  op: interpolate(f, [s, s + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  y:  interpolate(f, [s, s + 24], [55, 0], { easing: Easing.bezier(0.16, 1, 0.3, 1), extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
});

const photoScale = (f: number) =>
  interpolate(f, [0, SLIDE], [1.06, 1.0], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });

// ── Slide components ──────────────────────────────────────────────────────────

const S1Hook: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const topicWords = p.topic.split(" ");
  const mid = Math.ceil(topicWords.length / 2);
  const line1 = topicWords.slice(0, mid).join(" ");
  const line2 = topicWords.slice(mid).join(" ");

  const bar = interpolate(f, [5, 28], [0, 90], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const a1 = mkAnim(f, 6); const a2 = mkAnim(f, 20); const a3 = mkAnim(f, 48);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${photoScale(f)})`, transformOrigin: "center" }}>
        <Img src={staticFile("photos/carousel_0.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(6,6,16,.65) 0%,rgba(6,6,16,.1) 30%,rgba(6,6,16,.93) 100%)" }} />
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", bottom: 1920 - 1520, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ width: bar, height: 4, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 26, color: CYAN, textTransform: "uppercase", letterSpacing: 5 }}>{p.tag}</div>
        </div>
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 82, color: WHITE, lineHeight: 0.95, letterSpacing: "-3px" }}>{line1}</div>
          {line2 && <GradText size={82} spacing="-3px">{line2}</GradText>}
        </div>
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)`, marginTop: 6 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 30, color: WDIM }}>
            {p.stat_footnote}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const S2Stat: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const pct = interpolate(f, [20, 100], [0, p.stat_number], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const redP = interpolate(f, [20, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const numColor = `rgb(${Math.round(255 * redP)},${Math.round(212 - 180 * redP)},${Math.round(255 - 255 * redP)})`;
  const a1 = mkAnim(f, 8); const a2 = mkAnim(f, 26); const a3 = mkAnim(f, 104);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill>
        <Img src={staticFile("photos/carousel_1.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.2 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center,rgba(6,6,16,0) 0%,rgba(6,6,16,.88) 100%)" }} />
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", justifyContent: "center", gap: 18 }}>
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 32, color: WDIM }}>{p.stat_context.split(" ").slice(0, 5).join(" ")}</div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 200, color: numColor, lineHeight: 0.9, letterSpacing: "-8px" }}>{Math.round(pct)}</div>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 95, color: numColor, letterSpacing: "-3px", lineHeight: 0.9 }}>{p.stat_suffix}</div>
        </div>
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 46, color: WHITE, lineHeight: 1.1, letterSpacing: "-1px" }}>
            {p.stat_context.split(" ").slice(5).join(" ")}
          </div>
        </div>
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)`, marginTop: 6 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 28, color: WDIM }}>{p.stat_footnote}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const S3Solution: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const bar = interpolate(f, [6, 30], [0, 90], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const a1 = mkAnim(f, 8); const a2 = mkAnim(f, 24); const a3 = mkAnim(f, 48); const a4 = mkAnim(f, 72); const a5 = mkAnim(f, 96);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill>
        <Img src={staticFile("photos/carousel_2.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.22 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(6,6,16,.65) 0%,rgba(6,6,16,.3) 40%,rgba(6,6,16,.92) 100%)" }} />
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", bottom: 1920 - 1560, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ width: bar, height: 4, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 26, color: CYAN, textTransform: "uppercase", letterSpacing: 5 }}>La solución</div>
        </div>
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 76, color: WHITE, lineHeight: 0.95, letterSpacing: "-2px" }}>{p.solution_line1}</div>
          <GradText size={76} spacing="-2px">{p.solution_line2}</GradText>
        </div>
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 76, color: WHITE, lineHeight: 0.95, letterSpacing: "-2px" }}>{p.solution_word1}</div>
        </div>
        <div style={{ opacity: a4.op, transform: `translateY(${a4.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 76, color: WHITE, lineHeight: 0.95, letterSpacing: "-2px" }}>{p.solution_word2}</div>
        </div>
        <div style={{ opacity: a5.op, transform: `translateY(${a5.y}px)`, marginTop: 4 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 30, color: WDIM }}>{p.solution_sub}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const S4Vision: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const a1 = mkAnim(f, 8); const a2 = mkAnim(f, 28); const a3 = mkAnim(f, 54); const a4 = mkAnim(f, 80); const a5 = mkAnim(f, 106);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill>
        <Img src={staticFile("photos/carousel_3.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.2 }} />
      </AbsoluteFill>
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", justifyContent: "center", gap: 20 }}>
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 26, color: CYAN, textTransform: "uppercase", letterSpacing: 5 }}>Imagina esto</div>
        </div>
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 72, color: WHITE, lineHeight: 1.0, letterSpacing: "-2px" }}>{p.vision_hook}</div>
          <GradText size={72} spacing="-2px">{p.vision_result}</GradText>
        </div>
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)` }}>
          <div style={{ width: 70, height: 3, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
        </div>
        <div style={{ opacity: a4.op, transform: `translateY(${a4.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 34, color: WDIM, lineHeight: 1.45 }}>{p.vision_body}</div>
        </div>
        <div style={{ opacity: a5.op, transform: `translateY(${a5.y}px)` }}>
          <GradText size={34} spacing="-0.5px">{p.vision_brand}</GradText>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const S5Proof: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const bullets = [p.bullet1, p.bullet2, p.bullet3];
  const titleOp = interpolate(f, [8, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY  = interpolate(f, [8, 26], [50, 0], { easing: Easing.bezier(0.16, 1, 0.3, 1), extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill>
        <Img src={staticFile("photos/carousel_4.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.2 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(6,6,16,.7) 0%,rgba(6,6,16,.5) 50%,rgba(6,6,16,.9) 100%)" }} />
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", justifyContent: "center", gap: 36 }}>
        <div style={{ opacity: titleOp, transform: `translateY(${titleY}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 66, color: WHITE, lineHeight: 1.0, letterSpacing: "-1.5px" }}>Lo que dicen</div>
          <GradText size={66} spacing="-1.5px">nuestros clientes.</GradText>
          <div style={{ width: 70, height: 4, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2, marginTop: 14 }} />
        </div>
        {bullets.map((text, i) => {
          const op = interpolate(f, [32 + i * 18, 50 + i * 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const x  = interpolate(f, [32 + i * 18, 52 + i * 18], [-40, 0], { easing: Easing.bezier(0.16, 1, 0.3, 1), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ opacity: op, transform: `translateX(${x}px)`, display: "flex", gap: 16, alignItems: "flex-start" }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: `linear-gradient(135deg,${CYAN},${BLUE})`, flexShrink: 0, marginTop: 13 }} />
              <div style={{ fontFamily: MONT, fontWeight: 600, fontSize: 36, color: WHITE, lineHeight: 1.3, letterSpacing: "-0.5px" }}>{text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const S6CTA: React.FC<{ f: number; p: ZiaCarouselProps }> = ({ f, p }) => {
  const topicWords = p.topic.split(" ");
  const mid = Math.ceil(topicWords.length / 2);
  const line1 = topicWords.slice(0, mid).join(" ");
  const line2 = topicWords.slice(mid).join(" ");

  const ps = interpolate(f, [0, SLIDE], [1.05, 1.0], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bar = interpolate(f, [5, 26], [0, 100], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin((f / 30) * Math.PI * 1.4);
  const a1 = mkAnim(f, 8); const a2 = mkAnim(f, 26); const a3 = mkAnim(f, 50); const btn = mkAnim(f, 74); const sub = mkAnim(f, 96);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: BG }}>
      <AbsoluteFill style={{ transform: `scale(${ps})`, transformOrigin: "center" }}>
        <Img src={staticFile("photos/carousel_5.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.4 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(6,6,16,.65) 0%,rgba(6,6,16,.3) 35%,rgba(6,6,16,.92) 100%)" }} />
      <div style={{ position: "absolute", top: ST - 30, left: SL }}><Logo /></div>
      <div style={{ position: "absolute", top: ST + 20, left: SL, width: bar, height: 3, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, left: SL, right: 1080 - SR, display: "flex", flexDirection: "column", justifyContent: "center", gap: 16 }}>
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 26, color: CYAN, textTransform: "uppercase", letterSpacing: 4 }}>Empieza esta semana</div>
        </div>
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 80, color: WHITE, lineHeight: 0.95, letterSpacing: "-2.5px" }}>{line1}</div>
          {line2 && <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 80, color: WHITE, lineHeight: 0.95, letterSpacing: "-2.5px" }}>{line2}</div>}
        </div>
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)`, marginTop: 4 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 30, color: WDIM, lineHeight: 1.45 }}>{p.cta_sub}</div>
        </div>
        <div style={{ marginTop: 24, opacity: btn.op, transform: `translateY(${btn.y}px)` }}>
          <div style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            background: `linear-gradient(90deg,${CYAN},${BLUE})`,
            borderRadius: 16, padding: "22px 40px",
            boxShadow: `0 0 ${50 * glow}px rgba(0,212,255,${0.45 * glow}),0 0 ${22 * glow}px rgba(24,48,255,${0.35 * glow})`,
          }}>
            <span style={{ fontFamily: MONT, fontWeight: 900, fontSize: 36, color: WHITE, letterSpacing: "-0.5px" }}>{p.cta_button}</span>
          </div>
        </div>
        <div style={{ opacity: sub.op, marginTop: 8 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 24, color: WFAINT }}>ziautomate.com · Empieza en 48h</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Crossfade between slides ──────────────────────────────────────────────────
function slideOpacity(frame: number, slideIndex: number): number {
  const start = slideIndex * (SLIDE - TRANS);
  const end   = start + SLIDE;
  const fadeIn  = interpolate(frame, [start, start + TRANS], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = slideIndex < 5
    ? interpolate(frame, [end - TRANS, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 1;
  return Math.min(fadeIn, fadeOut);
}

// ── Main composition ──────────────────────────────────────────────────────────
export const ZiaCarousel: React.FC<ZiaCarouselProps> = (props) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {[S1Hook, S2Stat, S3Solution, S4Vision, S5Proof, S6CTA].map((Slide, i) => (
        <AbsoluteFill key={i} style={{ opacity: slideOpacity(frame, i) }}>
          <Slide f={frame - i * (SLIDE - TRANS)} p={props} />
        </AbsoluteFill>
      ))}
    </AbsoluteFill>
  );
};
