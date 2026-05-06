import React, { useMemo } from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
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
}

export const defaultZiaVideoProps: ZiaVideoProps = {
  topic: "Automatización IA para pymes",
  wordTimings: [],
  durationInSeconds: 30,
};

const YELLOW = "#FFE400";
const CYAN = "#00E5FF";
const FONT = "'Noto Sans', 'DejaVu Sans', Arial, sans-serif";
const SCENE_SECONDS = 3;
const WORDS_PER_GROUP = 3;

// ── CapCut-style viral captions ───────────────────────────────────────────────
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

  const currentIdx = timings.findIndex(
    (w) => t >= w.start - 0.05 && t <= w.end + 0.12
  );
  if (currentIdx === -1) return null;

  const groupIdx = Math.floor(currentIdx / WORDS_PER_GROUP);
  const group = wordGroups[groupIdx];
  if (!group) return null;

  const groupStartFrame = Math.round(group[0].start * fps);
  const elapsed = Math.max(0, frame - groupStartFrame);

  const popScale = spring({
    fps,
    frame: elapsed,
    config: { damping: 9, stiffness: 380, mass: 0.25 },
    from: 0.5,
    to: 1.0,
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 148,
        left: 16,
        right: 16,
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-end",
        flexWrap: "wrap",
        gap: "4px 12px",
        transform: `scale(${popScale})`,
        transformOrigin: "center bottom",
      }}
    >
      {group.map((w) => {
        const isCurrent = w === timings[currentIdx];
        return (
          <span
            key={`${w.start}`}
            style={{
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
              textShadow: isCurrent
                ? "none"
                : "2px 3px 0px #000, 0 0 24px rgba(0,0,0,0.95)",
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

// ── Main overlay composition (transparent bg) ─────────────────────────────────
export const ZiaVideo: React.FC<ZiaVideoProps> = ({
  topic,
  wordTimings,
  durationInSeconds,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const totalFrames = Math.ceil(durationInSeconds * fps);

  const sceneDuration = Math.round(fps * SCENE_SECONDS);
  const sceneIdx = Math.floor(frame / sceneDuration);
  const sceneFrame = frame - sceneIdx * sceneDuration;

  // White flash at every scene cut (skips first)
  const flashOpacity =
    sceneIdx === 0
      ? 0
      : interpolate(sceneFrame, [0, 2, 9], [0.75, 0.12, 0], {
          extrapolateRight: "clamp",
        });

  // Cinematic dark gradient (makes text readable over any video bg)
  const gradientOverlay =
    "linear-gradient(to bottom," +
    "rgba(0,4,18,0.82) 0%," +
    "rgba(0,4,18,0.18) 12%," +
    "rgba(0,4,18,0.04) 35%," +
    "rgba(0,4,18,0.08) 62%," +
    "rgba(0,4,18,0.60) 80%," +
    "rgba(0,4,18,0.95) 100%)";

  // UI fade-in
  const uiIn = interpolate(frame, [0, Math.round(fps * 0.4)], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  // Progress bar
  const progress = Math.min(1, t / durationInSeconds);

  // End-screen CTA (last 3 s)
  const ctaThreshold = Math.max(0, durationInSeconds - 3);
  const ctaSpring =
    durationInSeconds > 5
      ? spring({
          fps,
          frame: Math.max(0, frame - Math.round(ctaThreshold * fps)),
          config: { damping: 10, stiffness: 280, mass: 0.35 },
          from: 0,
          to: 1,
        })
      : 0;

  const showCTA = ctaSpring > 0.01;
  const showCaption = !showCTA || ctaSpring < 0.4;

  return (
    // No backgroundColor → fully transparent canvas
    <AbsoluteFill>

      {/* ══ Cinematic gradient overlay ══ */}
      <AbsoluteFill style={{ background: gradientOverlay }} />

      {/* ══ Cut flash ══ */}
      <AbsoluteFill
        style={{
          backgroundColor: "white",
          opacity: flashOpacity,
          pointerEvents: "none",
        }}
      />

      {/* ══ Progress bar ══ */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: 7,
          width: `${progress * 100}%`,
          background: `linear-gradient(to right,${CYAN},${YELLOW})`,
          boxShadow: `0 0 14px ${CYAN}, 0 0 7px ${YELLOW}`,
          zIndex: 60,
        }}
      />

      {/* ══ Brand pill ══ */}
      <div
        style={{
          position: "absolute",
          top: 18,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: uiIn,
        }}
      >
        <div
          style={{
            background: "rgba(0,4,22,0.75)",
            border: `2px solid ${CYAN}`,
            borderRadius: 50,
            padding: "10px 30px",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              backgroundColor: CYAN,
              boxShadow: `0 0 14px ${CYAN}`,
            }}
          />
          <span
            style={{
              color: CYAN,
              fontSize: 48,
              fontFamily: FONT,
              fontWeight: 800,
              letterSpacing: "0.05em",
            }}
          >
            ziautomate
          </span>
        </div>
      </div>

      {/* ══ Topic line ══ */}
      {topic && (
        <div
          style={{
            position: "absolute",
            top: 118,
            left: 40,
            right: 40,
            display: "flex",
            justifyContent: "center",
            opacity: uiIn,
          }}
        >
          <span
            style={{
              color: "rgba(255,255,255,0.90)",
              fontSize: 34,
              fontFamily: FONT,
              fontWeight: 700,
              textAlign: "center",
              textShadow: "1px 2px 10px rgba(0,0,0,0.95)",
              letterSpacing: "0.01em",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: 960,
            }}
          >
            {topic}
          </span>
        </div>
      )}

      {/* ══ Viral captions ══ */}
      {showCaption && (
        <ViralCaption t={t} timings={wordTimings} frame={frame} fps={fps} />
      )}

      {/* ══ End CTA ══ */}
      {showCTA && (
        <div
          style={{
            position: "absolute",
            bottom: 148,
            left: 24,
            right: 24,
            opacity: ctaSpring,
            transform: `scale(${ctaSpring})`,
            transformOrigin: "center bottom",
            background: YELLOW,
            borderRadius: 22,
            padding: "28px 36px 24px",
            textAlign: "center",
          }}
        >
          <span
            style={{
              display: "block",
              color: "#000000",
              fontSize: 76,
              fontFamily: FONT,
              fontWeight: 900,
              textTransform: "uppercase",
              lineHeight: 1.0,
              letterSpacing: "-0.02em",
            }}
          >
            ¿Quieres esto?
          </span>
          <span
            style={{
              display: "block",
              color: "#000000",
              fontSize: 42,
              fontFamily: FONT,
              fontWeight: 700,
              marginTop: 14,
            }}
          >
            ziautomate.netlify.app
          </span>
        </div>
      )}

      {/* ══ Footer bar ══ */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 112,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          background: "rgba(0,4,22,0.84)",
          borderTop: `3px solid ${CYAN}`,
          opacity: uiIn,
        }}
      >
        <span
          style={{
            color: CYAN,
            fontSize: 42,
            fontFamily: FONT,
            fontWeight: 700,
            letterSpacing: "0.04em",
          }}
        >
          ziautomate.netlify.app
        </span>
        <span
          style={{
            color: "rgba(100,155,180,0.85)",
            fontSize: 26,
            fontFamily: FONT,
            letterSpacing: "0.09em",
          }}
        >
          automatización · IA · pymes
        </span>
      </div>

    </AbsoluteFill>
  );
};
