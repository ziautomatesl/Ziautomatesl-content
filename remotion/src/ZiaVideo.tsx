import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export interface WordTiming {
  word: string;
  start: number;
  end: number;
}

export interface ZiaVideoProps {
  topic: string;
  wordTimings: WordTiming[];
  durationInSeconds: number;
  audioSrc: string;
}

export const defaultZiaVideoProps: ZiaVideoProps = {
  topic: "Automatización IA para pymes",
  wordTimings: [],
  durationInSeconds: 30,
  audioSrc: "audio.mp3",
};

const YELLOW = "#FFE400";
const CYAN = "#00E5FF";
const GREEN = "#00FF41";
const PURPLE = "#8B5CF6";
const FONT = "'Noto Sans', 'DejaVu Sans', Arial, sans-serif";
const SCENE_SECONDS = 3;
const WORDS_PER_GROUP = 3;
const W = 1080;
const H = 1920;

// ─────────────────────────────────────────────────────────────────────────────
// Theme 1: Neural Network
// ─────────────────────────────────────────────────────────────────────────────

const NEURAL_NODES = [
  { x: 180, y: 280 }, { x: 520, y: 140 }, { x: 860, y: 380 },
  { x: 290, y: 560 }, { x: 700, y: 620 }, { x: 120, y: 850 },
  { x: 940, y: 920 }, { x: 430, y: 1040 }, { x: 670, y: 1180 },
  { x: 200, y: 1380 }, { x: 820, y: 1320 }, { x: 500, y: 1600 },
  { x: 280, y: 1750 }, { x: 760, y: 1680 }, { x: 980, y: 1500 },
  { x: 640, y: 400 }, { x: 80, y: 1150 }, { x: 900, y: 200 },
  { x: 460, y: 850 }, { x: 350, y: 1900 },
];

const NEURAL_EDGES = [
  [0, 1], [0, 3], [0, 15], [1, 2], [1, 4], [1, 17],
  [2, 4], [2, 6], [2, 17], [3, 4], [3, 5], [3, 7],
  [4, 6], [4, 15], [4, 18], [5, 7], [5, 8], [5, 16],
  [6, 8], [6, 14], [7, 8], [7, 9], [7, 11], [7, 18],
  [8, 10], [8, 11], [9, 11], [9, 12], [9, 16],
  [10, 11], [10, 13], [10, 14], [11, 12], [11, 13],
  [12, 13], [13, 14], [14, 19], [15, 18],
];

const NeuralNet: React.FC<{ frame: number; fps: number }> = ({ frame }) => (
  <AbsoluteFill style={{ background: "linear-gradient(180deg, #000812 0%, #001428 100%)" }}>
    <svg width={W} height={H} style={{ position: "absolute" }}>
      {NEURAL_EDGES.map(([a, b], i) => {
        const na = NEURAL_NODES[a], nb = NEURAL_NODES[b];
        const edgeOp = 0.18 + 0.12 * Math.abs(Math.sin(frame * 0.04 + i * 0.41));
        const sigPhase = ((frame * 1.8 + i * 19) % 72) / 72;
        const sigX = na.x + (nb.x - na.x) * sigPhase;
        const sigY = na.y + (nb.y - na.y) * sigPhase;
        return (
          <g key={i}>
            <line x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
              stroke={CYAN} strokeWidth={1.5} opacity={edgeOp} />
            <circle cx={sigX} cy={sigY} r={5}
              fill={YELLOW} opacity={sigPhase > 0.9 ? 0 : 0.9} />
          </g>
        );
      })}
      {NEURAL_NODES.map((n, i) => {
        const pulse = Math.abs(Math.sin(frame * 0.08 + i * 0.7));
        const r = 10 + 5 * pulse;
        const isActive = ((frame + i * 11) % 48) < 6;
        return (
          <g key={i}>
            <circle cx={n.x} cy={n.y} r={r * 2.5} fill={CYAN} opacity={0.06} />
            <circle cx={n.x} cy={n.y} r={r}
              fill={isActive ? YELLOW : CYAN} opacity={0.6 + 0.4 * pulse} />
            <circle cx={n.x} cy={n.y} r={r * 0.4}
              fill="white" opacity={(0.6 + 0.4 * pulse) * 0.8} />
          </g>
        );
      })}
    </svg>
  </AbsoluteFill>
);

// ─────────────────────────────────────────────────────────────────────────────
// Theme 2: Matrix Data Rain
// ─────────────────────────────────────────────────────────────────────────────

const MATRIX_COLS = 18;
const COL_W = Math.floor(W / MATRIX_COLS);

const MatrixRain: React.FC<{ frame: number }> = ({ frame }) => (
  <AbsoluteFill style={{ background: "#000000" }}>
    <svg width={W} height={H} style={{ position: "absolute" }}>
      <defs>
        {Array.from({ length: MATRIX_COLS }, (_, i) => (
          <linearGradient key={i} id={`rg${i}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#000000" stopOpacity="0" />
            <stop offset="55%" stopColor={GREEN} stopOpacity="0.35" />
            <stop offset="100%" stopColor={GREEN} stopOpacity="1" />
          </linearGradient>
        ))}
      </defs>
      {Array.from({ length: MATRIX_COLS }, (_, i) => {
        const speed = 6 + (i % 5) * 2.4;
        const trailH = 200 + (i % 4) * 90;
        const headY = ((frame * speed + i * 137 + 400) % (H + 400)) - 200;
        const x = i * COL_W;
        const w = COL_W - 3;
        const op = 0.55 + 0.45 * Math.abs(Math.sin(i * 0.9));
        return (
          <g key={i} opacity={op}>
            <rect x={x + 2} y={headY - trailH} width={w} height={trailH}
              fill={`url(#rg${i})`} />
            <rect x={x} y={headY} width={w + 2} height={12}
              fill="white" opacity={0.95} />
            {[0.28, 0.56, 0.78].map((t, j) => (
              <rect key={j} x={x + 4} y={headY - trailH * t}
                width={w - 8} height={5} fill={GREEN} opacity={0.65} />
            ))}
          </g>
        );
      })}
    </svg>
  </AbsoluteFill>
);

// ─────────────────────────────────────────────────────────────────────────────
// Theme 3: Neon Grid / Circuit Scan
// ─────────────────────────────────────────────────────────────────────────────

const GRID = 108;

const NeonGrid: React.FC<{ frame: number }> = ({ frame }) => {
  const cols = Math.ceil(W / GRID) + 1;
  const rows = Math.ceil(H / GRID) + 1;
  const gridOp = 0.13 + 0.06 * Math.abs(Math.sin(frame * 0.06));
  const scanY = (frame * 7) % H;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #040010 0%, #0A0028 100%)" }}>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="scanFade" x1="0" x2="0" y1="1" y2="0">
            <stop offset="0%" stopColor={CYAN} stopOpacity="1" />
            <stop offset="100%" stopColor={CYAN} stopOpacity="0" />
          </linearGradient>
        </defs>
        {Array.from({ length: cols }, (_, i) => (
          <line key={`v${i}`} x1={i * GRID} y1={0} x2={i * GRID} y2={H}
            stroke={PURPLE} strokeWidth={1} opacity={gridOp} />
        ))}
        {Array.from({ length: rows }, (_, i) => (
          <line key={`h${i}`} x1={0} y1={i * GRID} x2={W} y2={i * GRID}
            stroke={CYAN} strokeWidth={1} opacity={gridOp} />
        ))}
        {Array.from({ length: cols }, (_, ci) =>
          Array.from({ length: rows }, (_, ri) => {
            const p = Math.abs(Math.sin(frame * 0.05 + ci * 0.41 + ri * 0.37));
            if (p < 0.82) return null;
            return <circle key={`${ci}-${ri}`} cx={ci * GRID} cy={ri * GRID}
              r={3} fill={CYAN} opacity={(p - 0.82) * 5.5 * 0.55} />;
          })
        )}
        {/* Scan line */}
        <rect x={0} y={scanY - 14} width={W} height={12}
          fill="url(#scanFade)" opacity={0.35} />
        <rect x={0} y={scanY - 2} width={W} height={4}
          fill={CYAN} opacity={0.8} />
        {/* Corner crosshairs */}
        {([[50, 50], [W - 50, 50], [50, H - 50], [W - 50, H - 50]] as [number, number][]).map(([cx, cy], i) => (
          <g key={i}>
            <line x1={cx - 24} y1={cy} x2={cx + 24} y2={cy}
              stroke={YELLOW} strokeWidth={2.5} opacity={0.7} />
            <line x1={cx} y1={cy - 24} x2={cx} y2={cy + 24}
              stroke={YELLOW} strokeWidth={2.5} opacity={0.7} />
            <circle cx={cx} cy={cy} r={6} fill="none"
              stroke={YELLOW} strokeWidth={1.5} opacity={0.5} />
          </g>
        ))}
      </svg>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Theme 4: Phone Chat Interface
// ─────────────────────────────────────────────────────────────────────────────

const CHAT_MSGS = [
  { text: "¿Cuánto cuesta contratar 5 personas?", user: true },
  { text: "Puedo automatizarlo por menos 💡", user: false },
  { text: "¿Y cuándo empezamos?", user: true },
  { text: "Ahora mismo. Sin código 🚀", user: false },
];

const PhoneChat: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const PW = 580, PH = 980;
  const px = (W - PW) / 2;
  const py = (H - PH) / 2;
  const DELAY = 16;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #0A0A1A 0%, #141430 100%)" }}>
      <div style={{
        position: "absolute",
        left: px, top: py, width: PW, height: PH,
        borderRadius: 50,
        background: "#111122",
        border: "3px solid rgba(0,229,255,0.3)",
        boxShadow: `0 0 70px rgba(0,229,255,0.12), 0 0 140px rgba(139,92,246,0.08)`,
        overflow: "hidden",
      }}>
        <div style={{
          height: 60, background: "#1A1A2E",
          display: "flex", alignItems: "center", justifyContent: "center",
          borderBottom: "1px solid rgba(0,229,255,0.2)",
        }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: GREEN, marginRight: 10 }} />
          <span style={{ color: CYAN, fontSize: 28, fontFamily: FONT, fontWeight: 700 }}>
            ZIA Assistant
          </span>
        </div>
        <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 18 }}>
          {CHAT_MSGS.map((msg, i) => {
            const elapsed = Math.max(0, frame - i * DELAY);
            const sc = spring({ fps, frame: elapsed,
              config: { damping: 10, stiffness: 300, mass: 0.3 }, from: 0, to: 1 });
            if (sc < 0.01) return null;
            return (
              <div key={i} style={{
                display: "flex", justifyContent: msg.user ? "flex-end" : "flex-start",
                opacity: sc, transform: `translateY(${(1 - sc) * 20}px)`,
              }}>
                <div style={{
                  maxWidth: "78%",
                  background: msg.user ? YELLOW : "#1E2A4A",
                  color: msg.user ? "#000" : "#fff",
                  borderRadius: msg.user ? "22px 22px 6px 22px" : "22px 22px 22px 6px",
                  padding: "16px 22px", fontSize: 31,
                  fontFamily: FONT, fontWeight: 600, lineHeight: 1.4,
                  border: msg.user ? "none" : `1px solid ${CYAN}33`,
                }}>
                  {msg.text}
                </div>
              </div>
            );
          })}
          {frame > CHAT_MSGS.length * DELAY && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{
                background: "#1E2A4A",
                borderRadius: "22px 22px 22px 6px",
                padding: "18px 28px", display: "flex", gap: 10, alignItems: "center",
                border: `1px solid ${CYAN}33`,
              }}>
                {[0, 8, 16].map((d) => (
                  <div key={d} style={{
                    width: 14, height: 14, borderRadius: "50%",
                    background: CYAN,
                    opacity: 0.3 + 0.7 * Math.abs(Math.sin((frame + d) * 0.15)),
                  }} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Theme 5: Stats Explosion
// ─────────────────────────────────────────────────────────────────────────────

const STATS = [
  { label: "Reducción de costes operativos", value: 87, suffix: "%" },
  { label: "Clientes gestionados por IA", value: 3, suffix: "x más" },
  { label: "Errores humanos eliminados", value: 0, suffix: "%" },
  { label: "Horas ahorradas por semana", value: 40, suffix: "h" },
];

const StatsBurst: React.FC<{ frame: number; fps: number; sceneIdx: number }> = ({ frame, fps, sceneIdx }) => {
  const stat = STATS[sceneIdx % STATS.length];
  const totalF = Math.round(SCENE_SECONDS * fps);

  const prog = interpolate(frame, [0, totalF * 0.65], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const numVal = Math.round(prog * stat.value);
  const sc = spring({ fps, frame,
    config: { damping: 8, stiffness: 200, mass: 0.4 }, from: 0.2, to: 1 });

  const BURST = 16;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #0A0A00 0%, #1A1400 100%)" }}>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        {Array.from({ length: BURST }, (_, i) => {
          const angle = (i / BURST) * Math.PI * 2;
          const len = 80 + prog * (160 + (i % 3) * 60);
          const op = interpolate(prog, [0, 0.2, 0.85, 1], [0, 0.8, 0.55, 0.35]);
          return (
            <line key={i}
              x1={W / 2} y1={H / 2}
              x2={W / 2 + Math.cos(angle) * len}
              y2={H / 2 + Math.sin(angle) * len}
              stroke={i % 2 === 0 ? YELLOW : CYAN}
              strokeWidth={3 - i % 2} opacity={op}
            />
          );
        })}
        {[0.3, 0.6, 0.9].map((t, i) => {
          const r = prog * 420 * t;
          const op = interpolate(prog, [t * 0.5, t, Math.min(1, t + 0.4)], [0, 0.5, 0]);
          return <circle key={i} cx={W / 2} cy={H / 2} r={r}
            fill="none" stroke={YELLOW} strokeWidth={2} opacity={op} />;
        })}
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", gap: 28,
      }}>
        <div style={{ transform: `scale(${sc})`, display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{
            fontSize: 230, fontFamily: FONT, fontWeight: 900, color: YELLOW,
            lineHeight: 1, textShadow: `0 0 50px ${YELLOW}80`,
          }}>
            {numVal}
          </span>
          <span style={{
            fontSize: 88, fontFamily: FONT, fontWeight: 900, color: YELLOW,
            lineHeight: 1, textShadow: `0 0 24px ${YELLOW}80`,
          }}>
            {stat.suffix}
          </span>
        </div>
        <span style={{
          color: "rgba(255,255,255,0.8)", fontSize: 50, fontFamily: FONT,
          fontWeight: 700, textAlign: "center", letterSpacing: "0.02em",
          opacity: prog, paddingLeft: 40, paddingRight: 40,
        }}>
          {stat.label}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Theme 6: Energy Pulse
// ─────────────────────────────────────────────────────────────────────────────

const EnergyPulse: React.FC<{ frame: number }> = ({ frame }) => {
  const CX = W / 2, CY = H / 2;
  const PERIOD = 48;
  const RINGS = 5;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #1A0020 0%, #050010 100%)" }}>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        {Array.from({ length: RINGS }, (_, i) => {
          const phase = ((frame + i * (PERIOD / RINGS)) % PERIOD) / PERIOD;
          const r = phase * 680;
          const op = Math.pow(1 - phase, 1.5) * 0.8;
          const sw = (1 - phase) * 5 + 1;
          return (
            <circle key={i} cx={CX} cy={CY} r={r}
              fill="none" stroke={i % 2 === 0 ? CYAN : PURPLE}
              strokeWidth={sw} opacity={op} />
          );
        })}
        {Array.from({ length: 8 }, (_, i) => {
          const angle = (i / 8) * Math.PI * 2 + frame * 0.016;
          const len = 120 + 30 * Math.abs(Math.sin(frame * 0.07 + i));
          return (
            <line key={i} x1={CX} y1={CY}
              x2={CX + Math.cos(angle) * len} y2={CY + Math.sin(angle) * len}
              stroke={CYAN} strokeWidth={2}
              opacity={0.2 + 0.2 * Math.abs(Math.sin(frame * 0.05 + i * 0.7))} />
          );
        })}
        {Array.from({ length: 12 }, (_, i) => {
          const angle = (i / 12) * Math.PI * 2 + frame * 0.008;
          const r1 = 160 + 20 * Math.sin(frame * 0.06 + i);
          const r2 = 340 + 40 * Math.sin(frame * 0.04 + i * 1.3);
          return (
            <line key={i}
              x1={CX + Math.cos(angle) * r1} y1={CY + Math.sin(angle) * r1}
              x2={CX + Math.cos(angle) * r2} y2={CY + Math.sin(angle) * r2}
              stroke={CYAN} strokeWidth={1.5}
              opacity={0.07 + 0.06 * Math.abs(Math.sin(frame * 0.05 + i))} />
          );
        })}
        <circle cx={CX} cy={CY} r={90} fill={PURPLE} opacity={0.28} />
        <circle cx={CX} cy={CY} r={55} fill={CYAN} opacity={0.38} />
        <circle cx={CX} cy={CY} r={28} fill="white" opacity={0.95} />
      </svg>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Theme router
// ─────────────────────────────────────────────────────────────────────────────

const Background: React.FC<{ sceneIdx: number; sceneFrame: number; fps: number }> = ({ sceneIdx, sceneFrame, fps }) => {
  switch (sceneIdx % 6) {
    case 0: return <NeuralNet frame={sceneFrame} fps={fps} />;
    case 1: return <MatrixRain frame={sceneFrame} />;
    case 2: return <NeonGrid frame={sceneFrame} />;
    case 3: return <PhoneChat frame={sceneFrame} fps={fps} />;
    case 4: return <StatsBurst frame={sceneFrame} fps={fps} sceneIdx={sceneIdx} />;
    case 5: return <EnergyPulse frame={sceneFrame} />;
    default: return <NeuralNet frame={sceneFrame} fps={fps} />;
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// CapCut-style viral captions
// ─────────────────────────────────────────────────────────────────────────────

const ViralCaption: React.FC<{
  t: number;
  timings: WordTiming[];
  frame: number;
  fps: number;
}> = ({ t, timings, frame, fps }) => {
  const wordGroups = useMemo(() => {
    const g: WordTiming[][] = [];
    for (let i = 0; i < timings.length; i += WORDS_PER_GROUP) {
      g.push(timings.slice(i, i + WORDS_PER_GROUP));
    }
    return g;
  }, [timings]);

  const currentIdx = timings.findIndex((w) => t >= w.start - 0.05 && t <= w.end + 0.12);
  if (currentIdx === -1) return null;

  const groupIdx = Math.floor(currentIdx / WORDS_PER_GROUP);
  const group = wordGroups[groupIdx];
  if (!group) return null;

  const groupStartFrame = Math.round(group[0].start * fps);
  const elapsed = Math.max(0, frame - groupStartFrame);

  const popScale = spring({
    fps, frame: elapsed,
    config: { damping: 9, stiffness: 380, mass: 0.25 },
    from: 0.5, to: 1.0,
  });

  return (
    <div style={{
      position: "absolute",
      bottom: 148,
      left: 16, right: 16,
      display: "flex",
      justifyContent: "center",
      alignItems: "flex-end",
      flexWrap: "wrap",
      gap: "4px 12px",
      transform: `scale(${popScale})`,
      transformOrigin: "center bottom",
    }}>
      {group.map((w) => {
        const isCurrent = w === timings[currentIdx];
        return (
          <span key={`${w.start}`} style={{
            display: "inline-block",
            fontSize: 98,
            fontFamily: FONT,
            fontWeight: 900,
            letterSpacing: "-0.01em",
            textTransform: "uppercase",
            lineHeight: 1.1,
            color: isCurrent ? "#000000" : "#FFFFFF",
            background: isCurrent ? YELLOW : "transparent",
            padding: isCurrent ? "4px 20px 8px" : "0",
            borderRadius: isCurrent ? 14 : 0,
            textShadow: isCurrent ? "none" : "2px 3px 0px #000, 0 0 24px rgba(0,0,0,0.95)",
          }}>
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Main composition
// ─────────────────────────────────────────────────────────────────────────────

export const ZiaVideo: React.FC<ZiaVideoProps> = ({
  topic, wordTimings, durationInSeconds, audioSrc,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const sceneDuration = Math.round(fps * SCENE_SECONDS);
  const sceneIdx = Math.floor(frame / sceneDuration);
  const sceneFrame = frame - sceneIdx * sceneDuration;

  const flashOpacity = sceneIdx === 0
    ? 0
    : interpolate(sceneFrame, [0, 2, 9], [0.7, 0.1, 0], { extrapolateRight: "clamp" });

  const uiIn = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const progress = Math.min(1, t / durationInSeconds);

  const ctaThreshold = Math.max(0, durationInSeconds - 3);
  const ctaSpring = durationInSeconds > 5
    ? spring({
        fps, frame: Math.max(0, frame - Math.round(ctaThreshold * fps)),
        config: { damping: 10, stiffness: 280, mass: 0.35 },
        from: 0, to: 1,
      })
    : 0;

  const showCTA = ctaSpring > 0.01;
  const showCaption = !showCTA || ctaSpring < 0.4;

  return (
    <AbsoluteFill>
      {/* Audio playback */}
      <Audio src={staticFile(audioSrc)} />

      {/* Programmatic background */}
      <Background sceneIdx={sceneIdx} sceneFrame={sceneFrame} fps={fps} />

      {/* Vignette for text readability */}
      <AbsoluteFill style={{
        background:
          "linear-gradient(to bottom," +
          "rgba(0,0,0,0.72) 0%," +
          "rgba(0,0,0,0.10) 18%," +
          "rgba(0,0,0,0.04) 45%," +
          "rgba(0,0,0,0.10) 65%," +
          "rgba(0,0,0,0.68) 82%," +
          "rgba(0,0,0,0.94) 100%)",
        pointerEvents: "none",
      }} />

      {/* Cut flash */}
      <AbsoluteFill style={{
        backgroundColor: "white", opacity: flashOpacity, pointerEvents: "none",
      }} />

      {/* Progress bar */}
      <div style={{
        position: "absolute", top: 0, left: 0,
        height: 7, width: `${progress * 100}%`,
        background: `linear-gradient(to right,${CYAN},${YELLOW})`,
        boxShadow: `0 0 14px ${CYAN}`,
        zIndex: 60,
      }} />

      {/* Brand pill */}
      <div style={{
        position: "absolute", top: 18, left: 0, right: 0,
        display: "flex", justifyContent: "center", opacity: uiIn,
      }}>
        <div style={{
          background: "rgba(0,0,20,0.75)",
          border: `2px solid ${CYAN}`,
          borderRadius: 50, padding: "10px 30px",
          display: "flex", alignItems: "center", gap: 12,
        }}>
          <div style={{
            width: 14, height: 14, borderRadius: "50%",
            backgroundColor: CYAN, boxShadow: `0 0 14px ${CYAN}`,
          }} />
          <span style={{
            color: CYAN, fontSize: 48, fontFamily: FONT,
            fontWeight: 800, letterSpacing: "0.05em",
          }}>
            ziautomate
          </span>
        </div>
      </div>

      {/* Topic label */}
      {topic && (
        <div style={{
          position: "absolute", top: 118, left: 40, right: 40,
          display: "flex", justifyContent: "center", opacity: uiIn,
        }}>
          <span style={{
            color: "rgba(255,255,255,0.90)", fontSize: 34,
            fontFamily: FONT, fontWeight: 700, textAlign: "center",
            textShadow: "1px 2px 10px rgba(0,0,0,0.95)",
            whiteSpace: "nowrap", overflow: "hidden",
            textOverflow: "ellipsis", maxWidth: 960,
          }}>
            {topic}
          </span>
        </div>
      )}

      {/* Viral captions */}
      {showCaption && (
        <ViralCaption t={t} timings={wordTimings} frame={frame} fps={fps} />
      )}

      {/* End CTA */}
      {showCTA && (
        <div style={{
          position: "absolute", bottom: 148, left: 24, right: 24,
          opacity: ctaSpring, transform: `scale(${ctaSpring})`,
          transformOrigin: "center bottom",
          background: YELLOW, borderRadius: 22,
          padding: "28px 36px 24px", textAlign: "center",
        }}>
          <span style={{
            display: "block", color: "#000000", fontSize: 76,
            fontFamily: FONT, fontWeight: 900, textTransform: "uppercase",
            lineHeight: 1.0, letterSpacing: "-0.02em",
          }}>
            ¿Quieres esto?
          </span>
          <span style={{
            display: "block", color: "#000000", fontSize: 42,
            fontFamily: FONT, fontWeight: 700, marginTop: 14,
          }}>
            ziautomate.netlify.app
          </span>
        </div>
      )}

      {/* Footer bar */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, height: 112,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", gap: 4,
        background: "rgba(0,0,20,0.84)", borderTop: `3px solid ${CYAN}`,
        opacity: uiIn,
      }}>
        <span style={{
          color: CYAN, fontSize: 42, fontFamily: FONT,
          fontWeight: 700, letterSpacing: "0.04em",
        }}>
          ziautomate.netlify.app
        </span>
        <span style={{
          color: "rgba(100,155,180,0.85)", fontSize: 26,
          fontFamily: FONT, letterSpacing: "0.09em",
        }}>
          automatización · IA · pymes
        </span>
      </div>
    </AbsoluteFill>
  );
};
