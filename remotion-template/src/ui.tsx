// ui.tsx — shared visual language: 清代舆图/工笔淡彩 paper style.
import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export const PALETTE = {
  paper: "#f2e8d5",
  paperDeep: "#e9dcc0",
  ink: "#3b2f23",
  inkSoft: "#6b5a44",
  ochre: "#a8452c", // 考古硬证据 赭红
  indigo: "#2f5d7c", // 文献记载 青黛
  legend: "#7c7291", // 民间传说 灰紫
  gold: "#b8860b",
};

export const TAG_COLORS: Record<string, string> = {
  考古硬证据: PALETTE.ochre,
  文献记载: PALETTE.indigo,
  民间传说: PALETTE.legend,
};

export const PaperBg: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(120% 100% at 20% 0%, #f7efdd 0%, " +
        PALETTE.paper + " 45%, " + PALETTE.paperDeep + " 100%)",
    }}
  >
    <div
      style={{
        position: "absolute", inset: 0,
        background:
          "repeating-linear-gradient(0deg, rgba(120,90,40,0.022) 0px, rgba(120,90,40,0.022) 1px, transparent 1px, transparent 7px), radial-gradient(90% 70% at 85% 100%, rgba(90,60,20,0.10), transparent 60%)",
      }}
    />
  </AbsoluteFill>
);

export const Corners: React.FC = () => {
  const base = "gaoliangqiao/ui/corner_";
  return (
    <>
      <Img src={staticFile(base + "top_left.png")} style={{ position: "absolute", top: 0, left: 0, width: 150 }} />
      <Img src={staticFile(base + "top_right.png")} style={{ position: "absolute", top: 0, right: 0, width: 150 }} />
      <Img src={staticFile(base + "bottom_left.png")} style={{ position: "absolute", bottom: 0, left: 0, width: 150 }} />
      <Img src={staticFile(base + "bottom_right.png")} style={{ position: "absolute", bottom: 0, right: 0, width: 150 }} />
    </>
  );
};

export const EvidenceTag: React.FC<{ label: string; delay?: number; small?: boolean }> = ({
  label, delay = 0, small,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - delay, fps, config: { damping: 12, stiffness: 160 } });
  const color = TAG_COLORS[label] ?? PALETTE.inkSoft;
  return (
    <div
      style={{
        display: "inline-block",
        transform: `translateY(${(1 - pop) * 18}px)`,
        opacity: pop,
        background: color,
        color: "#f7f0df",
        fontSize: small ? 20 : 24,
        fontWeight: 700,
        padding: small ? "4px 14px" : "7px 20px",
        borderRadius: 6,
        letterSpacing: 3,
        boxShadow: "0 3px 10px rgba(60,40,20,0.25)",
        border: "1px solid rgba(255,255,255,0.35)",
      }}
    >
      [{label}]
    </div>
  );
};

export const PageHeader: React.FC<{ title: string; subtitle?: string; pageNo: number; delay?: number; totalPages?: number }> = ({
  title, subtitle, pageNo, delay = 0, totalPages = 8,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - delay, fps, config: { damping: 14 } });
  return (
    <div
      style={{
        position: "absolute", top: 46, left: 110, right: 110,
        opacity: pop, transform: `translateY(${(1 - pop) * -20}px)`,
        display: "flex", alignItems: "center", gap: 24,
      }}
    >
      <Img src={staticFile("gaoliangqiao/ui/title_seal.png")} style={{ width: 84, height: 84 }} />
      <div>
        <div style={{ fontSize: 52, fontWeight: 800, color: PALETTE.ink, letterSpacing: 2, lineHeight: 1.15 }}>
          {title}
        </div>
        {subtitle ? (
          <div style={{ fontSize: 26, color: PALETTE.inkSoft, marginTop: 8, letterSpacing: 1 }}>{subtitle}</div>
        ) : null}
      </div>
      <div
        style={{
          marginLeft: "auto", fontSize: 26, color: PALETTE.inkSoft, fontWeight: 700,
          border: `2px solid ${PALETTE.inkSoft}`, borderRadius: 8, padding: "6px 16px", opacity: 0.85,
        }}
      >
        {pageNo} / {totalPages}
      </div>
    </div>
  );
};

// Wrapper: fade + rise + optional slight pop (for images/DOM blocks).
export const Enter: React.FC<{
  at: number; children: React.ReactNode; x?: number; y?: number; style?: React.CSSProperties;
}> = ({ at, children, x = 0, y = 26, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - at, fps, config: { damping: 16, stiffness: 120 } });
  return (
    <div
      style={{
        opacity: pop,
        transform: `translate(${(1 - pop) * x}px, ${(1 - pop) * y}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// KenBurns push-in on an image.
export const KenBurns: React.FC<{ src: string; at: number; from?: number; to?: number;
  style?: React.CSSProperties; durationInFrames: number }> = ({
  src, at, from = 1.0, to = 1.06, style, durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame - at, [0, durationInFrames], [from, to], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const fade = interpolate(frame - at, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Img
      src={staticFile(src)}
      style={{ ...style, opacity: fade, transform: `scale(${scale})`, transition: "none" }}
    />
  );
};

// Bottom caption bar synced via subtitles.ts (absolute seconds within page).
export const Caption: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: "absolute", bottom: 8, left: 0, right: 0,
      display: "flex", justifyContent: "center", pointerEvents: "none",
    }}
  >
    <div
      style={{
        maxWidth: 1500, background: "rgba(43,32,20,0.78)", color: "#f7f0df",
        fontSize: 40, fontWeight: 600, lineHeight: 1.4, letterSpacing: 2,
        padding: "14px 34px", borderRadius: 10, textAlign: "center",
        boxShadow: "0 6px 22px rgba(30,20,10,0.35)",
      }}
    >
      {text}
    </div>
  </div>
);

// Scaled beat helper: design second boundaries -> local frames for a page of
// `pageDur` seconds (design assumed `designDur` seconds).
export const scaled = (boundsSec: number[], designDur: number, pageDur: number, fps: number): number[] =>
  boundsSec.map((b) => Math.round((b / designDur) * pageDur * fps));

// Page-local captions driven by data/subtitles.ts (seconds within the page).
import { SUBTITLES, CaptionLine } from "./data/subtitles";

export const PageCaptions: React.FC<{ page: number }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lines: CaptionLine[] = SUBTITLES[page] ?? [];
  const t = frame / fps;
  const active = lines.find((l) => t >= l.from && t < l.from + l.dur);
  if (!active) return null;
  return <Caption text={active.text} />;
};
