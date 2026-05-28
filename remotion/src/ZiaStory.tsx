import React from "react";
import {
  AbsoluteFill, interpolate, useCurrentFrame, Easing, Img, staticFile,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Montserrat";

const { fontFamily: MONT } = loadFont("normal", { weights: ["400", "600", "700", "900"], subsets: ["latin"] });

const CYAN  = "#00d4ff";
const BLUE  = "#1830ff";
const WHITE = "#ffffff";
const WDIM  = "rgba(255,255,255,0.72)";
const BG    = "#060610";

export interface ZiaStoryProps {
  hook_label:  string;  // "PREGUNTA DEL DÍA"
  hook_line1:  string;  // "¿Cuántos clientes"
  hook_line2:  string;  // "pierdes cada noche?"
  hook_sub:    string;  // "Responde abajo — descubre cuánto te cuesta el silencio."
  stat_number: number;  // 78
  stat_suffix: string;  // "%"
  stat_label:  string;  // "de las ventas va al que responde primero."
  photo_index: number;  // 1-6
}

export const defaultZiaStoryProps: ZiaStoryProps = {
  hook_label:  "PREGUNTA DEL DÍA",
  hook_line1:  "¿Cuántos clientes",
  hook_line2:  "pierdes cada noche?",
  hook_sub:    "Responde abajo — descubre cuánto te cuesta el silencio.",
  stat_number: 78,
  stat_suffix: "%",
  stat_label:  "de las ventas va al negocio que responde primero.",
  photo_index: 1,
};

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

const anim = (f: number, start: number, dist = 48) => ({
  op: interpolate(f, [start, start + 22], [0, 1], clamp),
  y:  interpolate(f, [start, start + 26], [dist, 0], { easing: ease, ...clamp }),
});

export const ZiaStory: React.FC<ZiaStoryProps> = (p) => {
  const f = useCurrentFrame();

  const bgScale = interpolate(f, [0, 300], [1.08, 1.0], { easing: Easing.out(Easing.cubic), ...clamp });
  const barW    = interpolate(f, [6, 28], [0, 64], { easing: Easing.out(Easing.cubic), ...clamp });
  const statVal = interpolate(f, [130, 230], [0, p.stat_number], { easing: Easing.out(Easing.cubic), ...clamp });
  const redPct  = interpolate(f, [130, 230], [0, 1], clamp);
  const numClr  = `rgb(${Math.round(255 * redPct)},${Math.round(212 - 180 * redPct)},${Math.round(255 - 255 * redPct)})`;

  const a0 = anim(f,  5);
  const a1 = anim(f, 18);
  const a2 = anim(f, 40);
  const a3 = anim(f, 68);
  const a4 = anim(f, 98);
  const a5 = anim(f, 128);
  const a6 = anim(f, 200);

  const photo = staticFile("photos/story_0.jpg");

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {/* Background */}
      <AbsoluteFill style={{ transform: `scale(${bgScale})`, transformOrigin: "center top" }}>
        <Img src={photo} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.28 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,rgba(6,6,16,.72) 0%,rgba(6,6,16,.18) 30%,rgba(6,6,16,.94) 68%,rgba(6,6,16,1) 100%)" }} />

      {/* Content — stays within top 65% (max 1248px) so poll sticker fits below */}
      <div style={{
        position: "absolute", top: 0, left: 54, right: 54,
        height: 1240,
        display: "flex", flexDirection: "column",
        paddingTop: 88,
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 52 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: `linear-gradient(135deg,${CYAN},${BLUE})` }} />
          <span style={{
            fontFamily: MONT, fontWeight: 800, fontSize: 24, letterSpacing: 1,
            background: `linear-gradient(90deg,${CYAN},${BLUE})`,
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>ziautomate</span>
        </div>

        {/* Accent bar */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ width: barW, height: 4, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
        </div>

        {/* Label */}
        <div style={{ opacity: a0.op, transform: `translateY(${a0.y}px)`, marginBottom: 12 }}>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 22, color: CYAN, textTransform: "uppercase", letterSpacing: 5 }}>
            {p.hook_label}
          </div>
        </div>

        {/* Hook line 1 */}
        <div style={{ opacity: a1.op, transform: `translateY(${a1.y}px)`, marginBottom: 2 }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 80, color: WHITE, lineHeight: 0.95, letterSpacing: "-3px" }}>
            {p.hook_line1}
          </div>
        </div>

        {/* Hook line 2 — gradient */}
        <div style={{ opacity: a2.op, transform: `translateY(${a2.y}px)`, marginBottom: 22 }}>
          <div style={{
            fontFamily: MONT, fontWeight: 900, fontSize: 80, lineHeight: 0.95, letterSpacing: "-3px",
            background: `linear-gradient(90deg,${CYAN},${BLUE})`,
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>
            {p.hook_line2}
          </div>
        </div>

        {/* Sub */}
        <div style={{ opacity: a3.op, transform: `translateY(${a3.y}px)`, marginBottom: 32 }}>
          <div style={{ fontFamily: MONT, fontWeight: 400, fontSize: 28, color: WDIM, lineHeight: 1.4 }}>
            {p.hook_sub}
          </div>
        </div>

        {/* Divider */}
        <div style={{ opacity: a4.op, marginBottom: 24 }}>
          <div style={{ width: 50, height: 3, background: `linear-gradient(90deg,${CYAN},${BLUE})`, borderRadius: 2 }} />
        </div>

        {/* Stat number */}
        <div style={{ opacity: a5.op, transform: `translateY(${a5.y}px)`, display: "flex", alignItems: "baseline", gap: 6, marginBottom: 10 }}>
          <div style={{ fontFamily: MONT, fontWeight: 900, fontSize: 120, color: numClr, lineHeight: 0.9, letterSpacing: "-5px" }}>
            {Math.round(statVal)}
          </div>
          <div style={{ fontFamily: MONT, fontWeight: 700, fontSize: 60, color: numClr, letterSpacing: "-2px" }}>
            {p.stat_suffix}
          </div>
        </div>

        {/* Stat label */}
        <div style={{ opacity: a6.op, transform: `translateY(${a6.y}px)` }}>
          <div style={{ fontFamily: MONT, fontWeight: 600, fontSize: 30, color: WDIM, lineHeight: 1.35 }}>
            {p.stat_label}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
