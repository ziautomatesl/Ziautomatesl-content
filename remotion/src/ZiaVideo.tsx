import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
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
  audioSrc: string;
  wordTimings: WordTiming[];
  bgVideos: string[];
  durationInSeconds: number;
}

export const defaultZiaVideoProps: ZiaVideoProps = {
  topic: "Automatización IA para pymes",
  audioSrc: "audio.mp3",
  wordTimings: [],
  bgVideos: ["bg0.mp4"],
  durationInSeconds: 30,
};

const CYAN = "#00E5FF";
const FONT = "'Noto Sans', 'DejaVu Sans', Arial, sans-serif";

// ── Subtitle component ────────────────────────────────────────────────────────

const SubtitleArea: React.FC<{ t: number; timings: WordTiming[] }> = ({ t, timings }) => {
  const spoken = timings.filter((w) => w.start <= t + 0.06);
  const visible = spoken.slice(-7);
  if (visible.length === 0) return null;

  const currentWord = timings.find((w) => t >= w.start - 0.04 && t <= w.end + 0.10);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 128,
        left: 32,
        right: 32,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignContent: "flex-end",
        gap: "8px 14px",
        padding: "22px 30px 18px",
        background: "rgba(0, 4, 18, 0.80)",
        borderRadius: 24,
        border: "1.5px solid rgba(0, 180, 255, 0.25)",
      }}
    >
      {visible.map((w) => {
        const isCurrent = w === currentWord;
        const timeSinceStart = Math.max(0, t - w.start);
        const popScale =
          timeSinceStart < 0.1
            ? interpolate(timeSinceStart, [0, 0.1], [0.55, 1.0], {
                extrapolateRight: "clamp",
                easing: Easing.bezier(0.34, 1.56, 0.64, 1),
              })
            : 1.0;

        return (
          <span
            key={`${w.start}-${w.word}`}
            style={{
              display: "inline-block",
              fontSize: isCurrent ? 64 : 56,
              fontFamily: FONT,
              fontWeight: isCurrent ? 800 : 600,
              color: isCurrent ? CYAN : "rgba(255, 255, 255, 0.93)",
              textShadow: isCurrent
                ? `0 0 22px rgba(0, 229, 255, 0.65), 0 2px 8px rgba(0,0,0,0.9)`
                : "0 2px 6px rgba(0,0,0,0.85)",
              transform: `scale(${popScale})`,
              transformOrigin: "center bottom",
              lineHeight: 1.25,
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

// ── Background videos with cross-fade ────────────────────────────────────────

const BgVideos: React.FC<{ bgVideos: string[]; totalFrames: number; fps: number; frame: number }> = ({
  bgVideos,
  totalFrames,
  fps,
  frame,
}) => {
  if (bgVideos.length === 0) return null;

  const fadeFrames = Math.round(fps * 0.5); // 0.5s cross-fade
  const segFrames = Math.ceil(totalFrames / bgVideos.length);

  return (
    <>
      {bgVideos.map((src, i) => {
        const clipStart = i * segFrames;
        const seqFrom = i === 0 ? 0 : Math.max(0, clipStart - fadeFrames);
        const isLast = i === bgVideos.length - 1;
        const seqDuration = isLast ? totalFrames - seqFrom + fps : segFrames + fadeFrames;

        // Fade in (clips after first fade in over previous)
        const opacity =
          i === 0
            ? 1
            : interpolate(frame, [seqFrom, clipStart], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.ease,
              });

        return (
          <Sequence key={i} from={seqFrom} durationInFrames={seqDuration}>
            <AbsoluteFill style={{ opacity }}>
              <OffthreadVideo
                src={staticFile(src)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                loop
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </>
  );
};

// ── Main composition ──────────────────────────────────────────────────────────

export const ZiaVideo: React.FC<ZiaVideoProps> = ({
  topic,
  audioSrc,
  wordTimings,
  bgVideos,
  durationInSeconds,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const totalFrames = Math.ceil(durationInSeconds * fps);

  // Slow Ken Burns zoom on entire background
  const bgZoom = interpolate(frame, [0, totalFrames], [1.0, 1.07], {
    extrapolateRight: "clamp",
    easing: Easing.linear,
  });

  // UI elements fade in at start
  const uiOpacity = interpolate(frame, [0, Math.round(fps * 0.5)], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const topicLabel = topic.length > 40 ? topic.substring(0, 38) + "…" : topic;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000814", overflow: "hidden" }}>

      {/* ── Background videos (Ken Burns zoom) ── */}
      <AbsoluteFill
        style={{
          transform: `scale(${bgZoom})`,
          transformOrigin: "center center",
        }}
      >
        <BgVideos
          bgVideos={bgVideos}
          totalFrames={totalFrames}
          fps={fps}
          frame={frame}
        />
      </AbsoluteFill>

      {/* ── Cinematic gradient overlay ── */}
      <AbsoluteFill
        style={{
          background: [
            "linear-gradient(to bottom,",
            "  rgba(0,4,18,0.90) 0%,",
            "  rgba(0,4,18,0.30) 14%,",
            "  rgba(0,4,18,0.08) 35%,",
            "  rgba(0,4,18,0.12) 62%,",
            "  rgba(0,4,18,0.70) 82%,",
            "  rgba(0,4,18,0.95) 100%",
            ")",
          ].join(" "),
        }}
      />

      {/* ── Audio ── */}
      <Audio src={staticFile(audioSrc)} />

      {/* ── Header ── */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 128,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(0, 4, 22, 0.86)",
          borderBottom: `3px solid ${CYAN}`,
          opacity: uiOpacity,
        }}
      >
        <span
          style={{
            color: CYAN,
            fontSize: 82,
            fontFamily: FONT,
            fontWeight: 900,
            letterSpacing: "0.05em",
            textShadow: `0 0 40px rgba(0,229,255,0.45)`,
          }}
        >
          ziautomate
        </span>
      </div>

      {/* ── Topic badge ── */}
      {topic && (
        <div
          style={{
            position: "absolute",
            top: 146,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            opacity: uiOpacity,
          }}
        >
          <div
            style={{
              background: "rgba(0, 30, 80, 0.60)",
              border: "1.5px solid rgba(0, 180, 255, 0.40)",
              borderRadius: 32,
              padding: "10px 32px",
            }}
          >
            <span
              style={{
                color: CYAN,
                fontSize: 34,
                fontFamily: FONT,
                fontWeight: 700,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              {topicLabel}
            </span>
          </div>
        </div>
      )}

      {/* ── Subtitles ── */}
      <SubtitleArea t={t} timings={wordTimings} />

      {/* ── Footer ── */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 118,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          background: "rgba(0, 4, 22, 0.86)",
          borderTop: `3px solid ${CYAN}`,
          opacity: uiOpacity,
        }}
      >
        <span
          style={{
            color: CYAN,
            fontSize: 44,
            fontFamily: FONT,
            fontWeight: 700,
            letterSpacing: "0.04em",
          }}
        >
          ziautomate.netlify.app
        </span>
        <span
          style={{
            color: "rgba(100, 155, 180, 0.88)",
            fontSize: 28,
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
