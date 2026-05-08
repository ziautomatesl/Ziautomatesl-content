import React, { useMemo } from "react";
import * as THREE from "three";
import {
  AbsoluteFill, Audio, interpolate, spring, Sequence,
  staticFile, useCurrentFrame, useVideoConfig, Easing,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { LightLeak } from "@remotion/light-leaks";

export interface WordTiming { word: string; start: number; end: number; }
export interface ZiaVideoProps {
  topic: string; wordTimings: WordTiming[];
  durationInSeconds: number; audioSrc: string; seed: number;
}
export const defaultZiaVideoProps: ZiaVideoProps = {
  topic: "Tu negocio en piloto automático",
  wordTimings: [], durationInSeconds: 30, audioSrc: "audio.mp3", seed: 0,
};

// ─── Brand ────────────────────────────────────────────────────────────────────
const BLUE   = "#1a6bff";
const CYAN   = "#00e5ff";
const PURPLE = "#7c3aed";
const WHITE  = "#ffffff";
const TEXT   = "#d8dce8";
const BRAND_GRADIENT = `linear-gradient(135deg, ${CYAN} 0%, ${BLUE} 55%, ${PURPLE} 100%)`;
const FONT      = "'Inter', 'Noto Sans', Arial, sans-serif";
const FONT_HEAD = "'Space Grotesk', 'Inter', 'Noto Sans', Arial, sans-serif";
const SCENE_SECONDS = 3;
const W = 1080, H = 1920;

const BrandFonts: React.FC = () => (
  <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Grotesk:wght@500;600;700;800&display=swap');`}</style>
);

// ─── Ad scenes ───────────────────────────────────────────────────────────────
type SceneData = {
  stat: string | null; statPre: string; statNum: number | null; statSuf: string;
  headline: string; sub: string; words: string[];
};

// Escenas 2-7: dos variantes que rotan según seed para que cada video sea distinto
const TAIL_A: SceneData[] = [
  { stat: "+300%", statPre: "+", statNum: 300, statSuf: "%",
    headline: "más clientes", sub: "En solo 48 horas de implementación",
    words: ["+300%", "más", "clientes", "en", "48h"] },
  { stat: "24/7", statPre: "", statNum: null, statSuf: "",
    headline: "sin descanso", sub: "Tu IA trabaja mientras tú vives",
    words: ["24/7", "sin", "descanso", "nunca", "para"] },
  { stat: null, statPre: "", statNum: null, statSuf: "",
    headline: "Automatiza · Escala · Domina", sub: "Sin contratar más personal",
    words: ["Automatiza", "Escala", "Domina"] },
  { stat: "€599", statPre: "€", statNum: 599, statSuf: "/mes",
    headline: "todo incluido", sub: "IA · marketing · webs · automatización",
    words: ["€599/mes", "todo", "incluido"] },
  { stat: "4.2x", statPre: "", statNum: 4.2, statSuf: "x",
    headline: "más retorno", sub: "En publicidad digital con IA",
    words: ["4.2x", "más", "retorno", "con", "IA"] },
  { stat: "GRATIS", statPre: "", statNum: null, statSuf: "",
    headline: "Primera consulta", sub: "ziautomate.netlify.app · Reserva ahora",
    words: ["Primera", "consulta", "GRATIS"] },
];

const TAIL_B: SceneData[] = [
  { stat: "2h", statPre: "", statNum: 2, statSuf: "h/día",
    headline: "de trabajo recuperadas", sub: "Automatizando tareas repetitivas",
    words: ["2h/día", "de", "trabajo", "libre"] },
  { stat: "100%", statPre: "", statNum: 100, statSuf: "%",
    headline: "automático", sub: "Sin tocar nada, sin contratar a nadie",
    words: ["100%", "automático", "sin", "esfuerzo"] },
  { stat: null, statPre: "", statNum: null, statSuf: "",
    headline: "Capta · Convierte · Fideliza", sub: "El ciclo completo con IA",
    words: ["Capta", "Convierte", "Fideliza"] },
  { stat: "48h", statPre: "", statNum: null, statSuf: "",
    headline: "de implementación", sub: "Listo y funcionando en 2 días",
    words: ["En", "48h", "funcionando"] },
  { stat: "-80%", statPre: "-", statNum: 80, statSuf: "%",
    headline: "menos tiempo manual", sub: "Más tiempo para lo que importa",
    words: ["-80%", "tiempo", "manual"] },
  { stat: "GRATIS", statPre: "", statNum: null, statSuf: "",
    headline: "Primera sesión", sub: "ziautomate.netlify.app · Sin compromiso",
    words: ["Sesión", "GRATIS", "ahora"] },
];

// Escena 1 dinámica: usa el topic generado por IA
function buildScenes(topic: string, seed: number): SceneData[] {
  const topicWords = topic.split(" ").slice(0, 6);
  const tail = seed % 2 === 0 ? TAIL_A : TAIL_B;
  return [
    { stat: null, statPre: "", statNum: null, statSuf: "",
      headline: topic || "¿Tu negocio trabaja sin parar?",
      sub: "Hay una solución más inteligente",
      words: topicWords.length >= 2 ? topicWords : ["Automatiza", "tu", "negocio"] },
    ...tail,
  ];
}

// ─── Ad overlay ───────────────────────────────────────────────────────────────
const AdOverlay: React.FC<{ scenes: SceneData[]; sceneIdx: number; frame: number; fps: number; sceneDuration: number }> = ({
  scenes, sceneIdx, frame, fps, sceneDuration,
}) => {
  const scene = scenes[sceneIdx % scenes.length];

  const countProg = interpolate(frame, [4, 52], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.bezier(0.45, 0, 0.55, 1),
  });
  const statSc = spring({ fps, frame, config: { damping: 9, stiffness: 260, mass: 0.48 }, from: 0, to: 1 });
  const subIn  = interpolate(frame, [24, 42], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const statDisplay: string | null = (() => {
    if (!scene.stat) return null;
    if (scene.statNum === null) return scene.stat;
    const val = scene.statNum * countProg;
    return `${scene.statPre}${Number.isInteger(scene.statNum) ? Math.round(val) : val.toFixed(1)}${scene.statSuf}`;
  })();

  const hasStat = statDisplay !== null;
  const headlineWords = scene.headline.split(" ");

  const PAGE = 3;
  const words = scene.words;
  const numPages = Math.ceil(words.length / PAGE);
  const pageFrames = (sceneDuration * 0.84) / numPages;
  const pageIdx = Math.min(numPages - 1, Math.floor(frame / pageFrames));
  const pageFrame = frame - pageIdx * pageFrames;
  const page = words.slice(pageIdx * PAGE, (pageIdx + 1) * PAGE);
  const wInterval = pageFrames / (PAGE + 0.5);
  const activeWi = Math.min(page.length - 1, Math.floor(pageFrame / wInterval));

  return (
    <>
      <div style={{
        position: "absolute", top: hasStat ? "26%" : "33%",
        left: 44, right: 44, display: "flex", flexDirection: "column",
        alignItems: "center", gap: 18,
      }}>
        {hasStat && (
          <div style={{
            transform: `scale(${statSc})`,
            fontSize: statDisplay!.length > 5 ? 148 : statDisplay!.length > 3 ? 182 : 220,
            fontFamily: FONT_HEAD, fontWeight: 900, lineHeight: 0.95, textAlign: "center",
            background: BRAND_GRADIENT, WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent", backgroundClip: "text",
            filter: `drop-shadow(0 0 40px rgba(0,229,255,0.35)) drop-shadow(0 0 80px rgba(26,107,255,0.2))`,
          }}>
            {statDisplay}
          </div>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "5px 12px", lineHeight: 1.15, textAlign: "center" }}>
          {headlineWords.map((word, i) => {
            const wIn = interpolate(frame, [i * 9, i * 9 + 16], [0, 1], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
              easing: Easing.bezier(0.16, 1, 0.3, 1),
            });
            return (
              <span key={i} style={{
                display: "inline-block",
                fontSize: hasStat ? 76 : 92, fontFamily: FONT_HEAD, fontWeight: 800,
                color: WHITE, textShadow: "2px 3px 0 rgba(0,0,0,0.92), 0 0 32px rgba(0,0,0,0.85)",
                opacity: wIn, transform: `translateY(${(1 - wIn) * 24}px)`,
              }}>
                {word}
              </span>
            );
          })}
        </div>

        <div style={{
          color: TEXT, fontSize: 36, fontFamily: FONT, fontWeight: 600,
          textAlign: "center", opacity: subIn,
          textShadow: "1px 2px 10px rgba(0,0,0,0.98)", maxWidth: 900, letterSpacing: "0.01em",
        }}>
          {scene.sub}
        </div>

        {scene.stat === "GRATIS" && (
          <div style={{
            opacity: spring({ fps, frame: Math.max(0, frame - 20), config: { damping: 10, stiffness: 300, mass: 0.3 }, from: 0, to: 1 }),
            transform: `scale(${spring({ fps, frame: Math.max(0, frame - 20), config: { damping: 10, stiffness: 300, mass: 0.3 }, from: 0, to: 1 })})`,
            background: BRAND_GRADIENT, borderRadius: 20, padding: "22px 50px",
            boxShadow: `0 0 50px rgba(0,229,255,0.4), 0 0 100px rgba(26,107,255,0.25)`, marginTop: 8,
          }}>
            <span style={{ color: WHITE, fontSize: 44, fontFamily: FONT_HEAD, fontWeight: 800 }}>
              Reserva tu consulta ahora →
            </span>
          </div>
        )}
      </div>

      <div style={{
        position: "absolute", bottom: 180, left: 20, right: 20,
        display: "flex", justifyContent: "center", flexWrap: "wrap", gap: "4px 10px", minHeight: 100,
      }}>
        {page.map((word, wi) => {
          const wProg = interpolate(pageFrame, [wi * wInterval - 4, wi * wInterval + 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
            easing: Easing.bezier(0.34, 1.56, 0.64, 1),
          });
          const isActive = wi === activeWi;
          return (
            <span key={`${pageIdx}-${wi}`} style={{
              display: "inline-block", fontSize: 74, fontFamily: FONT_HEAD, fontWeight: 800,
              textTransform: "uppercase", lineHeight: 1.12, letterSpacing: "-0.02em",
              opacity: wProg, transform: `scale(${1 - (1 - wProg) * 0.28})`,
              transformOrigin: "center bottom",
              color: isActive ? "#03010a" : WHITE,
              background: isActive ? BRAND_GRADIENT : "transparent",
              padding: isActive ? "5px 22px 9px" : "0",
              borderRadius: isActive ? 13 : 0,
              textShadow: isActive ? "none" : "2px 3px 0 rgba(0,0,0,0.95), 0 0 28px rgba(0,0,0,0.9)",
              boxShadow: isActive ? `0 0 30px rgba(26,107,255,0.55)` : "none",
            }}>
              {word}
            </span>
          );
        })}
      </div>
    </>
  );
};

// ─── Aurora shader (skill: ShaderMaterial for radial gradient soft blobs) ─────
const AURORA_VERT = `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }
`;
const AURORA_FRAG = `
  varying vec2 vUv;
  uniform vec3 uColor;
  uniform float uAlpha;
  void main() {
    float d = length(vUv - vec2(0.5)) * 2.0;
    float a = pow(clamp(1.0 - d, 0.0, 1.0), 2.2) * uAlpha;
    gl_FragColor = vec4(uColor * a, a);
  }
`;

const C_PURPLE = new THREE.Color(0.49, 0.23, 0.93);
const C_BLUE   = new THREE.Color(0.10, 0.42, 1.00);
const C_CYAN   = new THREE.Color(0.00, 0.90, 1.00);

interface BlobProps { color: THREE.Color; x: number; y: number; scale: number; alpha: number; }
const AuroraBlob: React.FC<BlobProps> = ({ color, x, y, scale, alpha }) => {
  const mat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: color }, uAlpha: { value: alpha } },
    vertexShader: AURORA_VERT, fragmentShader: AURORA_FRAG,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  }), []);
  mat.uniforms.uColor.value = color;
  mat.uniforms.uAlpha.value = alpha;
  return (
    <mesh position={[x, y, -9]} scale={[scale, scale, 1]}>
      <planeGeometry args={[2, 2]} />
      <primitive object={mat} attach="material" />
    </mesh>
  );
};

// ─── Particle system (skill: BufferGeometry + AdditiveBlending driven by frame) ─
const N = 2500;

function sr(s: number): number { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

// Static per-particle data, computed once at module load (seeded, deterministic)
const P_BASE = new Float32Array(N * 3);
const P_COL  = new Float32Array(N * 3);
const P_SPD  = new Float32Array(N);
const P_PHS  = new Float32Array(N);
const P_AMP  = new Float32Array(N);
const CT = [[0.00, 0.90, 1.00], [0.10, 0.42, 1.00], [0.49, 0.23, 0.93], [1.00, 1.00, 1.00]];

(() => {
  for (let i = 0; i < N; i++) {
    const r  = 1.5 + sr(i * 7) * 7.5;
    const th = Math.acos(2 * sr(i * 7 + 1) - 1);
    const ph = sr(i * 7 + 2) * Math.PI * 2;
    P_BASE[i*3]   = r * Math.sin(th) * Math.cos(ph);
    P_BASE[i*3+1] = r * Math.sin(th) * Math.sin(ph) * 1.8; // stretch Y for portrait
    P_BASE[i*3+2] = r * Math.cos(th) * 0.5;
    P_SPD[i] = 0.25 + sr(i * 7 + 3) * 0.55;
    P_PHS[i] = sr(i * 7 + 4) * Math.PI * 2;
    P_AMP[i] = 0.04 + sr(i * 7 + 5) * 0.18;
    const t  = sr(i * 7 + 6);
    const ci = t < 0.4 ? 0 : t < 0.65 ? 1 : t < 0.85 ? 2 : 3;
    P_COL[i*3] = CT[ci][0]; P_COL[i*3+1] = CT[ci][1]; P_COL[i*3+2] = CT[ci][2];
  }
})();

const ParticleCloud: React.FC<{ frame: number }> = ({ frame }) => {
  const t = frame * 0.005;
  const positions = useMemo(() => {
    const arr = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      const s = P_SPD[i], p = P_PHS[i], a = P_AMP[i];
      arr[i*3]   = P_BASE[i*3]   + Math.sin(t * s + p) * a;
      arr[i*3+1] = P_BASE[i*3+1] + Math.cos(t * s * 0.7 + p + 1) * a * 0.4;
      arr[i*3+2] = P_BASE[i*3+2] + Math.sin(t * s * 0.5 + p + 2) * a * 0.15;
    }
    return arr;
  }, [t]);

  return (
    <points rotation={[0.12, t * 0.014, 0]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[P_COL, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.055} sizeAttenuation vertexColors
        transparent opacity={0.80}
        blending={THREE.AdditiveBlending} depthWrite={false}
      />
    </points>
  );
};

// ─── Per-scene aurora configs: [c1, a1, s1, c2, a2, s2, c3, a3, s3] ─────────
// Each scene has 3 blobs with different dominant colors, alphas and scales
const C_WHITE = new THREE.Color(0.85, 0.90, 1.00);
const C_ROSE  = new THREE.Color(0.90, 0.20, 0.65);

type BlobCfg = [THREE.Color, number, number]; // [color, alpha, scale]
const SCENE_AURORAS: [BlobCfg, BlobCfg, BlobCfg][] = [
  // 0 — intro: púrpura fuerte
  [[C_PURPLE, 0.68, 9.5], [C_BLUE,   0.40, 10.0], [C_CYAN,   0.22, 6.0]],
  // 1 — +300%: azul eléctrico dominante
  [[C_BLUE,   0.72, 11.0], [C_CYAN,  0.55, 7.5],  [C_PURPLE, 0.25, 8.0]],
  // 2 — 24/7: cian frío, casi monocromático
  [[C_CYAN,   0.70, 9.0], [C_BLUE,   0.45, 12.0], [C_WHITE,  0.18, 5.5]],
  // 3 — automatiza: mezcla equilibrada, más espaciado
  [[C_PURPLE, 0.55, 12.0], [C_BLUE,  0.55, 9.0],  [C_CYAN,   0.45, 7.0]],
  // 4 — €599: azul profundo + toque púrpura
  [[C_BLUE,   0.65, 13.0], [C_PURPLE,0.50, 8.5],  [C_CYAN,   0.28, 6.5]],
  // 5 — 4.2x: cian brillante + rosa acento
  [[C_CYAN,   0.65, 8.0], [C_BLUE,   0.50, 11.0], [C_ROSE,   0.30, 6.0]],
  // 6 — GRATIS: todos los colores al máximo para el CTA
  [[C_CYAN,   0.75, 9.0], [C_PURPLE, 0.65, 11.0], [C_BLUE,   0.60, 8.0]],
];

// ─── Ad background: dark + aurora (per-scene) + particles ─────────────────────
const AdBackground: React.FC<{ frame: number; sceneIdx: number }> = ({ frame, sceneIdx }) => {
  const t = frame * 0.004;
  const cfg = SCENE_AURORAS[sceneIdx % SCENE_AURORAS.length];
  const [b1, b2, b3] = cfg;

  // Aurora blob positions animated from frame (different motion per blob)
  const p1x = Math.sin(t * 0.50) * 2.2,         p1y = 4.0 + Math.cos(t * 0.40) * 1.8;
  const p2x = -2.0 + Math.cos(t * 0.35) * 2.5,  p2y = -3.5 + Math.sin(t * 0.45) * 2.0;
  const p3x = 2.5 + Math.sin(t * 0.60 + 1.5) * 1.8, p3y = 1.0 + Math.cos(t * 0.30 + 0.8) * 2.2;

  return (
    <AbsoluteFill>
      <ThreeCanvas width={W} height={H}>
        <color attach="background" args={["#03010a"]} />

        {/* Aurora blobs — color and intensity vary per scene */}
        <AuroraBlob color={b1[0]} x={p1x} y={p1y} scale={b1[2]} alpha={b1[1]} />
        <AuroraBlob color={b2[0]} x={p2x} y={p2y} scale={b2[2]} alpha={b2[1]} />
        <AuroraBlob color={b3[0]} x={p3x} y={p3y} scale={b3[2]} alpha={b3[1]} />

        {/* 2500-particle galaxy — continuous across all scenes */}
        <ParticleCloud frame={frame} />
      </ThreeCanvas>

      {/* Faint tech grid */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: [
          "linear-gradient(rgba(0,229,255,0.028) 1px, transparent 1px)",
          "linear-gradient(90deg, rgba(0,229,255,0.028) 1px, transparent 1px)",
        ].join(","),
        backgroundSize: "88px 88px",
      }} />
    </AbsoluteFill>
  );
};

// ─── Main composition ─────────────────────────────────────────────────────────
export const ZiaVideo: React.FC<ZiaVideoProps> = ({ topic, wordTimings, durationInSeconds, audioSrc, seed }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const scenes = buildScenes(topic, seed ?? 0);
  const sceneDuration = Math.round(fps * SCENE_SECONDS);
  const sceneIdx  = Math.floor(frame / sceneDuration);
  const sceneFrame = frame - sceneIdx * sceneDuration;

  const uiIn = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const progress    = Math.min(1, t / durationInSeconds);
  const totalFrames = Math.round(durationInSeconds * fps);
  const numScenes   = Math.ceil(totalFrames / sceneDuration);

  return (
    <AbsoluteFill>
      <BrandFonts />
      {audioSrc && <Audio src={staticFile(audioSrc)} />}

      {/* Ad background — aurora colors shift per scene */}
      <AdBackground frame={frame} sceneIdx={sceneIdx} />

      {/* Vignette — top/bottom darkening for text readability */}
      <AbsoluteFill style={{
        background: "linear-gradient(to bottom," +
          "rgba(0,0,0,0.82) 0%,rgba(0,0,0,0.12) 14%," +
          "rgba(0,0,0,0.04) 38%,rgba(0,0,0,0.10) 62%," +
          "rgba(0,0,0,0.78) 82%,rgba(0,0,0,0.97) 100%)",
        pointerEvents: "none",
      }} />

      {/* Skill: LightLeak overlays at every scene cut */}
      {Array.from({ length: numScenes - 1 }, (_, i) => {
        const cutFrame = (i + 1) * sceneDuration;
        if (cutFrame >= totalFrames) return null;
        return (
          <Sequence key={i} from={Math.max(0, cutFrame - 10)} durationInFrames={26}>
            <LightLeak durationInFrames={26} seed={(i * 5 + (seed ?? 0)) % 20}
              hueShift={[240, 0, 120, 200, 60, 300][i % 6]} />
          </Sequence>
        );
      })}

      {/* Progress bar */}
      <div style={{
        position: "absolute", top: 0, left: 0, height: 4,
        width: `${progress * 100}%`, background: BRAND_GRADIENT,
        boxShadow: `0 0 14px ${CYAN}`, zIndex: 60,
      }} />

      {/* Brand pill */}
      <div style={{ position: "absolute", top: 22, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: uiIn, zIndex: 10 }}>
        <div style={{
          background: "rgba(3,1,10,0.85)", border: `1.5px solid rgba(0,229,255,0.28)`,
          borderRadius: 50, padding: "12px 34px", display: "flex", alignItems: "center", gap: 14,
          boxShadow: `0 0 24px rgba(0,229,255,0.08)`,
        }}>
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: BRAND_GRADIENT, boxShadow: `0 0 10px ${CYAN}` }} />
          <span style={{
            fontSize: 48, fontFamily: FONT_HEAD, fontWeight: 800, letterSpacing: "-0.5px",
            background: BRAND_GRADIENT, WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent", backgroundClip: "text",
          }}>ziautomate</span>
        </div>
      </div>

      {/* Ad content: stat + headline + CapCut captions */}
      <AdOverlay scenes={scenes} sceneIdx={sceneIdx} frame={sceneFrame} fps={fps} sceneDuration={sceneDuration} />

      {/* Footer */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, height: 120,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 5,
        background: "rgba(3,1,10,0.94)", borderTop: `1px solid rgba(0,229,255,0.12)`,
        opacity: uiIn, zIndex: 10,
      }}>
        <span style={{
          fontSize: 44, fontFamily: FONT_HEAD, fontWeight: 800, letterSpacing: "-0.5px",
          background: BRAND_GRADIENT, WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent", backgroundClip: "text",
        }}>ziautomate.netlify.app</span>
        <span style={{ color: "rgba(90,102,128,0.9)", fontSize: 24, fontFamily: FONT, letterSpacing: "0.08em", fontWeight: 500 }}>
          automatización · IA · marketing · webs
        </span>
      </div>
    </AbsoluteFill>
  );
};
