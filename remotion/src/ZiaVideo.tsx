import React, { useMemo } from "react";
import * as THREE from "three";
import {
  AbsoluteFill, Audio, interpolate, spring, Sequence,
  staticFile, useCurrentFrame, useVideoConfig, Easing,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { LightLeak } from "@remotion/light-leaks";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption } from "@remotion/captions";

export interface WordTiming { word: string; start: number; end: number; }
export interface ZiaVideoProps {
  topic: string; wordTimings: WordTiming[];
  durationInSeconds: number; audioSrc: string; seed: number;
  highlights?: string[];
}
export const defaultZiaVideoProps: ZiaVideoProps = {
  topic: "Tu negocio en piloto automático",
  wordTimings: [], durationInSeconds: 30, audioSrc: "audio.mp3", seed: 0,
  highlights: ["AUTOMATIZA", "SIN CÓDIGO", "IA 24/7", "MÁS CLIENTES"],
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

// ─── Skill: TikTok-style captions using real wordTimings ─────────────────────
// Converts our WordTiming format to Caption format required by @remotion/captions
function toCaptions(wordTimings: WordTiming[]): Caption[] {
  return wordTimings.map((wt) => ({
    text: " " + wt.word,          // leading space as per skill whitespace rule
    startMs: wt.start * 1000,
    endMs: wt.end * 1000,
    timestampMs: wt.start * 1000,
    confidence: null,
  }));
}

const SWITCH_MS = 1400; // ~3 words per page

// Skill: caption page — timing de la skill + estilo visual CapCut
const CaptionPage: React.FC<{ page: ReturnType<typeof createTikTokStyleCaptions>["pages"][number] }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const absoluteTimeMs = page.startMs + (frame / fps) * 1000;

  // Skill: spring entrance de la página (timing.md — organic entrance)
  const pageIn = spring({ fps, frame, config: { damping: 14, stiffness: 320, mass: 0.35 }, from: 0, to: 1 });

  return (
    <div style={{
      position: "absolute", top: "50%", left: 20, right: 20,
      display: "flex", justifyContent: "center", flexWrap: "wrap",
      gap: "6px 8px", whiteSpace: "pre",
      opacity: pageIn,
      transform: `translateY(calc(-50% + ${(1 - pageIn) * 24}px))`,
    }}>
      {page.tokens.map((token, i) => {
        const isActive = token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;

        // Skill: stagger por palabra con playful overshoot (timing.md)
        const wordIn = interpolate(frame, [i * 5, i * 5 + 12], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
          easing: Easing.bezier(0.34, 1.56, 0.64, 1),
        });

        // Skill: spring scale en palabra activa (spring para movimiento orgánico)
        const activeSc = spring({ fps, frame, config: { damping: 9, stiffness: 300, mass: 0.38 }, from: 1, to: isActive ? 1.1 : 1 });

        return (
          <span key={token.fromMs} style={{
            display: "inline-block",
            fontSize: 92, fontFamily: FONT_HEAD, fontWeight: 800,
            textTransform: "uppercase", lineHeight: 1.15, letterSpacing: "-0.02em",
            whiteSpace: "pre",
            opacity: wordIn,
            transform: `scale(${isActive ? activeSc : 1}) translateY(${(1 - wordIn) * 22}px)`,
            transformOrigin: "center bottom",
            color: isActive ? "#03010a" : WHITE,
            background: isActive ? BRAND_GRADIENT : "transparent",
            padding: isActive ? "6px 26px 11px" : "0",
            borderRadius: isActive ? 16 : 0,
            textShadow: isActive ? "none" : "2px 3px 0 rgba(0,0,0,0.95), 0 0 28px rgba(0,0,0,0.9)",
            boxShadow: isActive ? "0 0 36px rgba(26,107,255,0.6)" : "none",
          }}>
            {token.text}
          </span>
        );
      })}
    </div>
  );
};

// Skill: renders all caption pages as Sequences, each timed to the audio
const SyncedCaptions: React.FC<{ wordTimings: WordTiming[] }> = ({ wordTimings }) => {
  const { fps } = useVideoConfig();

  const pages = useMemo(() => {
    if (!wordTimings.length) return [];
    const captions = toCaptions(wordTimings);
    return createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: SWITCH_MS }).pages;
  }, [wordTimings]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {pages.map((page, i) => {
        const next = pages[i + 1] ?? null;
        const startFrame = Math.floor((page.startMs / 1000) * fps);
        const endFrame   = next
          ? Math.floor((next.startMs / 1000) * fps)
          : startFrame + Math.ceil((SWITCH_MS / 1000) * fps);
        const dur = Math.max(1, endFrame - startFrame);
        return (
          <Sequence key={i} from={startFrame} durationInFrames={dur}>
            <CaptionPage page={page} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

// ─── Dynamic highlight — rota cada escena mostrando frases de impacto ─────────
const DynamicHighlight: React.FC<{ highlights: string[]; sceneIdx: number }> = ({ highlights, sceneIdx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!highlights.length) return null;

  const text = highlights[sceneIdx % highlights.length];
  const localFrame = frame % Math.round(fps * SCENE_SECONDS);

  const enter = spring({ fps, frame: localFrame, config: { damping: 13, stiffness: 260, mass: 0.45 }, from: 0, to: 1 });
  const glowPulse = 0.5 + Math.sin(frame * 0.12) * 0.25;

  const words = text.split(" ");
  return (
    <div style={{
      position: "absolute", top: "12%", left: 30, right: 30,
      display: "flex", flexWrap: "wrap", justifyContent: "center",
      gap: "4px 10px", zIndex: 5,
    }}>
      {words.map((word, i) => {
        const wIn = interpolate(localFrame, [i * 6, i * 6 + 14], [0, 1], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
          easing: Easing.bezier(0.34, 1.56, 0.64, 1),
        });
        return (
          <span key={i} style={{
            display: "inline-block",
            fontSize: text.length > 12 ? 100 : 128,
            fontFamily: FONT_HEAD, fontWeight: 900,
            textTransform: "uppercase", letterSpacing: "-0.03em",
            lineHeight: 1.0, textAlign: "center",
            background: BRAND_GRADIENT,
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
            opacity: wIn,
            transform: `scale(${0.72 + wIn * 0.28}) translateY(${(1 - wIn) * 32}px)`,
            filter: `drop-shadow(0 0 ${44 * glowPulse * enter}px rgba(0,229,255,0.8))`,
          }}>
            {word}
          </span>
        );
      })}
    </div>
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

// ─── 3D wave grid — malla que se ondula como una superficie digital ────────────
const SEGS_X = 32, SEGS_Y = 52;
const GRID_W = 16, GRID_H = 30;
const GRID_NX = SEGS_X + 1, GRID_NY = SEGS_Y + 1;

const WaveGrid: React.FC<{ frame: number; sceneIdx: number }> = ({ frame, sceneIdx }) => {
  const t = frame * 0.005;
  const cfg = SCENE_AURORAS[sceneIdx % SCENE_AURORAS.length];
  const gridColor = cfg[0][0];

  const linePositions = useMemo(() => {
    const grid = new Float32Array(GRID_NX * GRID_NY * 3);
    for (let iy = 0; iy < GRID_NY; iy++) {
      for (let ix = 0; ix < GRID_NX; ix++) {
        const x = (ix / SEGS_X - 0.5) * GRID_W;
        const y = (iy / SEGS_Y - 0.5) * GRID_H;
        const z = Math.sin(x * 0.55 + t) * Math.cos(y * 0.38 + t * 0.72) * 1.3
                + Math.sin(x * 0.30 + y * 0.24 + t * 1.10) * 0.55;
        const i = (iy * GRID_NX + ix) * 3;
        grid[i] = x; grid[i + 1] = y; grid[i + 2] = z;
      }
    }
    const lines: number[] = [];
    for (let iy = 0; iy < GRID_NY; iy++) {
      for (let ix = 0; ix < SEGS_X; ix++) {
        const i0 = (iy * GRID_NX + ix) * 3, i1 = i0 + 3;
        lines.push(grid[i0], grid[i0 + 1], grid[i0 + 2], grid[i1], grid[i1 + 1], grid[i1 + 2]);
      }
    }
    for (let ix = 0; ix < GRID_NX; ix++) {
      for (let iy = 0; iy < SEGS_Y; iy++) {
        const i0 = (iy * GRID_NX + ix) * 3, i1 = ((iy + 1) * GRID_NX + ix) * 3;
        lines.push(grid[i0], grid[i0 + 1], grid[i0 + 2], grid[i1], grid[i1 + 1], grid[i1 + 2]);
      }
    }
    return new Float32Array(lines);
  }, [t]);

  return (
    <lineSegments rotation={[-Math.PI * 0.30, t * 0.016, t * 0.004]} position={[0, -1.5, -3.5]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial color={gridColor} transparent opacity={0.16} />
    </lineSegments>
  );
};

// ─── Ad background: dark + aurora (per-scene) + wave grid + particles ──────────
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

        {/* 3D wave grid — malla ondulante digital */}
        <WaveGrid frame={frame} sceneIdx={sceneIdx} />

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
export const ZiaVideo: React.FC<ZiaVideoProps> = ({ topic, wordTimings, durationInSeconds, audioSrc, seed, highlights }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const uiIn = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const progress    = Math.min(1, t / durationInSeconds);
  const totalFrames = Math.round(durationInSeconds * fps);

  // Aurora scene index: changes every 3s for color variety
  const sceneDuration = Math.round(fps * SCENE_SECONDS);
  const sceneIdx = Math.floor(frame / sceneDuration);

  // LightLeaks every 3s
  const numScenes = Math.ceil(totalFrames / sceneDuration);

  return (
    <AbsoluteFill>
      <BrandFonts />
      {audioSrc && <Audio src={staticFile(audioSrc)} />}

      {/* Aurora + particle background — colors shift every 3s */}
      <AdBackground frame={frame} sceneIdx={sceneIdx} />

      {/* Vignette */}
      <AbsoluteFill style={{
        background: "linear-gradient(to bottom," +
          "rgba(0,0,0,0.82) 0%,rgba(0,0,0,0.12) 14%," +
          "rgba(0,0,0,0.04) 38%,rgba(0,0,0,0.10) 62%," +
          "rgba(0,0,0,0.78) 82%,rgba(0,0,0,0.97) 100%)",
        pointerEvents: "none",
      }} />

      {/* Skill: LightLeak at every 3s color shift */}
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

      {/* Frases de impacto que rotan cada escena */}
      <DynamicHighlight highlights={highlights ?? []} sceneIdx={sceneIdx} />

      {/* Skill: captions sincronizados al audio real con wordTimings */}
      <SyncedCaptions wordTimings={wordTimings} />

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
