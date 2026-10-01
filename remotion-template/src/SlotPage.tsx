import React, { useMemo } from "react";
import { AbsoluteFill, Img, staticFile, useVideoConfig } from "remotion";
import { PaperBg, EvidenceTag, PageCaptions, scaled, PALETTE } from "./ui";
import SLOTS_RAW from "./data/slots.json";

const SLOTS = SLOTS_RAW as Record<string, { plate: number[]; slots: Array<{ x: number; y: number; w: number; h: number }> }>;
import { PAGE_CONFIG, TextItem } from "./data/pages.config";
import { audioBeats } from "./data/narration";
import { PAGE_DURATIONS_SEC } from "./data/pageMap";

// --- resolution handling: single source of truth is the plate pixel space ---
const CANVAS = { w: 1920, h: 1080 };
// 板面目录名。改这一行即可换集。板面放 public/<EPISODE>/page_0N_layout.png
const EPISODE = "landianchang";
const plateScale = (plate: number[], canvas: { w: number; h: number }) => {
  // objectFit:"cover" mapping, exact
  // 板面 PNG 是 1672×941（≈16:9），cover 到 1920×1080 后板面里的框
  // 回到设计坐标，故槽位按 1:1 放画布即可。plate 声明的 1920×1080
  // 是"设计空间"，不是板面像素——两者在此重合。
  const s = Math.max(canvas.w / plate[0], canvas.h / plate[1]);
  return { s, ox: (canvas.w - plate[0] * s) / 2, oy: (canvas.h - plate[1] * s) / 2 };
};

const tagStyle: React.CSSProperties = { textAlign: "center" };

const FitText: React.FC<{
  text: string; boxW: number; boxH: number; size: number; color: string;
  weight?: number; ls?: number; lh?: number; max?: number; sub?: React.ReactNode; vertical?: boolean;
}> = ({ text, boxW, boxH, size, color, weight = 800, ls = 0, lh, max, sub, vertical }) => {
  const lineHeight = lh ?? 1.25;
  const hasManualBreak = text.includes(String.fromCharCode(10));
  const effW = (t: string) => Math.max(4, [...t].length - (t.match(/[0-9a-zA-Z .·／/]/g) || []).length * 0.45);
  const byWidth = hasManualBreak
    ? Math.min(...text.split(String.fromCharCode(10)).filter(Boolean).map((l) => (boxW - 24) / effW(l)))
    : (boxW - 24) / effW(text);
  const maxLines = hasManualBreak ? text.split(String.fromCharCode(10)).filter(Boolean).length : Math.ceil((size * effW(text)) / (boxW - 24));
  const byHeight = (boxH - 16) / (maxLines * lineHeight);
  const wraps = (f: number) => {
    if (hasManualBreak) {
      return text.split(String.fromCharCode(10)).filter(Boolean).every((l) => f * effW(l) <= boxW - 20);
    }
    const w = f * effW(text);
    const lines = Math.max(1, Math.ceil(w / Math.max(60, boxW - 24)));
    return lines * f * lineHeight <= boxH - 16;
  };
  let fsFit = Math.min(size, max ?? 99, byWidth, byHeight);
  while (fsFit > 14 && !wraps(fsFit)) fsFit -= 1;
  const vChars = [...text].filter((c) => c.charCodeAt(0) !== 10).length;
  const vFit = (() => {
    for (let f = size; f >= 13; f -= 1) {
      const cols = Math.ceil((vChars * f * 1.06) / Math.max(40, boxH - 26));
      if (cols * (f * 1.16) <= boxW - 18) return f;
    }
    return 13;
  })();
  const fs = vertical ? vFit : Math.max(15, Math.floor(fsFit));
  // sub 也要不溢出：按其最长行宽独立定字号
  const subFs = (() => {
    if (!sub || typeof sub !== "string") return 0;
    const lines = sub.split(String.fromCharCode(10)).filter(Boolean);
    if (!lines.length) return 0;
    const need = Math.min(...lines.map((l) => (boxW - 20) / effW(l)));
    return Math.max(12, Math.min(Math.floor(fs * 0.72), Math.floor(need)));
  })();
  return (
    <div style={vertical
      ? { writingMode: "vertical-rl", maxHeight: "100%", maxWidth: "100%", display: "flex", flexDirection: "row", alignItems: "center", justifyContent: "center" }
      : { textAlign: "center" }}>
      <div style={{ fontSize: fs, fontWeight: weight, color, letterSpacing: vertical ? "0.06em" : ls, lineHeight: lh ?? 1.25, textAlign: vertical ? "start" : "center" }}>{text}</div>
      {sub ? <div style={{ fontSize: subFs || Math.max(16, fs * 0.72), color: PALETTE.inkSoft, marginTop: fs * 0.25, textAlign: "center", lineHeight: 1.35 }}>{sub}</div> : null}
    </div>
  );
};

const TagChip: React.FC<{ label: string }> = ({ label }) => (
  <div style={tagStyle}><EvidenceTag label={label} small /></div>
);

export const PlatePage: React.FC<{ page: number }> = ({ page }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const key = `p${String(page).padStart(2, "0")}`;
  const cfg = PAGE_CONFIG[page];
  const det = SLOTS[key];
  // 2026-09-30 修正：useVideoConfig().durationInFrames 是「整部视频」的帧数
  // （本片 5756 帧 = 191.87s），不是当前 Sequence 的页长。
  // 原式 pageDur = durationInFrames / fps 得到 191.87s，
  // 使 anchor 退化为「整片时长」，末两项的 at 被推到几十秒后，整页内永远进不了场
  // —— 表现为 P4 的 wanshou_note / legend 消失且不随帧号补齐。
  // 正确：页长由 PAGE_DURATIONS_SEC 累加得出（与 Series.Sequence 一致）。
  const pageDur = useMemo(() => {
    const idx = Math.min(Math.max(page, 1), PAGE_DURATIONS_SEC.length) - 1;
    return PAGE_DURATIONS_SEC.slice(0, idx + 1).reduce((a, b) => a + b, 0);
  }, [page]);
  const { s, ox, oy } = plateScale(det.plate, CANVAS);
  const boxOf = (ref: string) => {
    const sl = (det.slots as Array<{ id: string; x: number; y: number; w: number; h: number }>).find((x) => x.id === ref);
    if (!sl) return { left: 0, top: 0, width: 10, height: 10 };
    return { left: ox + sl.x * s, top: oy + sl.y * s, width: sl.w * s, height: sl.h * s };
  };
  const box = (slotIdx: number) => {
    const sl = det.slots[slotIdx];
    return { left: ox + sl.x * s, top: oy + sl.y * s, width: sl.w * s, height: sl.h * s };
  };
  return (
    <AbsoluteFill>
      <PaperBg />
      <Img
        src={staticFile(`${EPISODE}/page_${String(page).padStart(2, "0")}_layout.png`)}
        style={{ position: "absolute", inset: 0, width: CANVAS.w, height: CANVAS.h, objectFit: "cover" }}
      />
      {cfg.items.map((it, idx) => {
        const nA = Math.max(cfg.items.length, 6);
        // 文本出场锚定"音频时长"而非页面时长：页尾 1.6s 留白期内所有元素必须已入场，
        // 否则最后一两项永远赶不上终态帧（E8 P5 实测踩中）。
        // 2026-09-30 修正两处：
        //  1) beats 的 from/dur 已是帧，原式 (from+dur)/fps 把帧当秒再除，anchor 缩到 0.8s，
        //     导致十几项挤在前 10 帧、末两项在整页内都追不上 → P4 少渲 wanshou_note/legend。
        //  2) 再留 1.2s 缓冲（页尾留白 1.6s），保证最后一项在纯音频结束前 1.2s 已入场。
        const audioFrames = audioBeats(page).reduce((mx, b) => Math.max(mx, b.from + b.dur), 0);
        const audio = audioFrames / fps;
        const anchorFrames = Math.max(1, Math.min(audio || pageDur, pageDur - 1.2) * fps - fps * 0.5);
        const at = Math.round((Math.min(idx, nA - 1) / (nA - 1)) * anchorFrames) + (it.delay ?? 0);
        const style: React.CSSProperties = it.manual
          ? { position: "absolute", ...it.manual }
          : { position: "absolute", ...boxOf(it.slotId!), display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" };
        if (it.backing) {
          style.background = it.backing === true || it.backing === "card" ? "rgba(247,240,223,0.92)" : String(it.backing);
          style.padding = "10px 12px";
          style.overflow = "hidden";
          style.boxSizing = "border-box";
          style.borderRadius = 12;
          style.boxShadow = "0 4px 14px rgba(60,40,20,0.18)";
        }
        return (
          <Enter key={idx} at={at} y={16} style={style}>
            {it.kind === "tag" ? (
              <TagChip label={it.text} />
            ) : (
              <FitText
                text={it.text}
                boxW={it.manual ? (it.manual.width ?? 400) : boxOf(it.slotId!).width}
                boxH={it.manual ? (it.manual.height ?? 120) : boxOf(it.slotId!).height}
                size={it.size ?? 28}
                color={it.color ?? PALETTE.ink}
                weight={it.weight ?? 800}
                ls={it.ls ?? 0}
                lh={it.lh}
                vertical={(it as { vertical?: boolean }).vertical}
                max={it.maxSize}
                sub={it.sub}
              />
            )}
          </Enter>
        );
      })}
      <PageCaptions page={page} />
    </AbsoluteFill>
  );
};

// local Enter re-export guard (ui.Enter used via wrapper below)
import { Enter } from "./ui";
