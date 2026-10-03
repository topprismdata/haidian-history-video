// SlotPage.tsx — E23《挂甲屯·杨六郎传说与清初额驸城》槽位渲染器。
// 板型（design.md v1.0）：MapPage = 全幅地图/叠合视口打底 + 文字槽（P3/P6/P8）；
// MixedPage = 纸底 + 真图装裱 + 页面内嵌示意 + HTML 卡（P1/P2/P4/P5/P7）。
// 坐标链与 qa_v2.geometry 严格同源：slots.json 全部页 plate = [1920,1080]（设计空间，
// 与画布 1:1 恒等映射），槽位坐标即画布坐标意图，不做第二次换算。
//
// E21 红线落地：
// 1) 物理隔离：所有浮在地图/照片上方的文字项一律 backing: true
//    （rgba(247,240,223,0.95) 卡纸垫），文字墨迹绝不与底图粘连；
// 2) 全幅视口（PanZoom/CrossFade/索引示意）由页面组件打底，
//    不占槽位——凡声明为槽位的图框一律 kind: "photo"，QA 自动排除；
// 3) 标记物（呼吸圈/点位）纯 SVG 叠加层（label 置空，命名走 tag 槽），不写 slots.json；
// 4) 槽位 id 写错不静默兜底，直接 throw（E11 实测：静默兜底框 = 文案飞画外）。
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { PALETTE, PaperBg, PhotoFrame, EvidenceTag, Enter } from "./ui";
import SLOTS_RAW from "./data/slots.json";
import { PAGE_CONFIG, TextItem } from "./data/pages.config";

const CANVAS = { w: 1920, h: 1080 };
const EPISODE = "guajiatun"; // 真图/图层目录 public/weigongcun/（sources.csv 同目录留档）

const useSlotBoxes = (page: number) => {
  const det = (SLOTS_RAW as Record<string, {
    plate: number[];
    slots: Array<{ id: string; x: number; y: number; w: number; h: number }>;
  }>)[`p${String(page).padStart(2, "0")}`];
  if (!det) throw new Error(`${EPISODE}: slots.json 缺少 p${String(page).padStart(2, "0")}`);
  const cfg = PAGE_CONFIG[page];
  if (!cfg) throw new Error(`${EPISODE}: pages.config.ts 缺少第 ${page} 页`);
  const boxOf = (ref: string) => {
    const sl = det.slots.find((x) => x.id === ref);
    if (!sl) throw new Error(`${EPISODE} p${page}: 槽位 "${ref}" 不存在（现有：${det.slots.map((x) => x.id).join(", ")}）`);
    return { left: sl.x, top: sl.y, width: sl.w, height: sl.h };
  };
  return { det, cfg, boxOf };
};

// 窄字符估宽（ASCII/标点 0.55 个汉字宽）——与 qa_v2.checks_data._text_units 同口径。
const CHAR_W = (c: string) => (/[0-9a-zA-Z .·／/]/.test(c) ? 0.55 : 1);

// FitBlock：支持手动 \n 断行的贪心折行 + 字号收缩（15px 下限）。
const fitFontSize = (
  text: string, boxW: number, boxH: number, size: number, lh: number,
): number => {
  const lines = text.split("\n");
  for (let fs = size; fs > 15; fs -= 1) {
    let total = 0;
    for (const ln of lines) {
      if (!ln) { total += 1; continue; }
      const units = [...ln].reduce((a, c) => a + CHAR_W(c), 0);
      total += Math.max(1, Math.ceil((units * fs) / boxW));
    }
    if (total * fs * lh <= boxH) return fs;
  }
  return 15;
};

export const FitBlock: React.FC<{
  text: string; boxW: number; boxH: number; size: number;
  color?: string; weight?: number; lh?: number; align?: "center" | "left";
}> = ({ text, boxW, boxH, size, color = PALETTE.ink, weight = 700, lh = 1.4, align = "center" }) => {
  const fs = fitFontSize(text, boxW, boxH, size, lh);
  return (
    <div
      style={{
        width: "100%", height: "100%",
        display: "flex", flexDirection: "column",
        alignItems: align === "center" ? "center" : "flex-start",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          fontSize: fs, lineHeight: lh, color, fontWeight: weight,
          whiteSpace: "pre-line", textAlign: align, width: "100%",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// ── 图框/示意图槽 ────────────────────────────────────────────────────
// frame = PhotoFrame 统一装裱（真图，来源条常显，contain 永不裁切）；
// strip = 板面/切片条（PNG，cover 铺满槽位）；
// node  = 页面内嵌示意节点（SVG 等 React 节点，细墨框衬底）——
//         制作组示意图专用，仍走 kind:"photo" 槽，QA 自动排除。
export type PhotoSpec =
  | { mode: "frame"; src: string; caption: string }
  | { mode: "strip"; src: string }
  | { mode: "node"; node: React.ReactNode };

const PhotoSlot: React.FC<{ spec: PhotoSpec; b: { left: number; top: number; width: number; height: number } }> = ({ spec, b }) => {
  if (spec.mode === "frame") {
    const width = Math.round(b.width);
    const pad = width >= 1200 ? 24 : width >= 700 ? 24 : width >= 460 ? 20 : 16;
    const displayH = Math.round(b.height - pad * 2 - 34);
    return (
      <PhotoFrame
        src={spec.src}
        caption={spec.caption}
        width={width}
        height={displayH}
        left={Math.round(b.left)}
        top={Math.round(b.top)}
      />
    );
  }
  if (spec.mode === "strip") {
    return (
      <div
        style={{
          position: "absolute", left: b.left, top: b.top, width: b.width, height: b.height,
          borderRadius: 14, overflow: "hidden", boxShadow: "0 6px 18px rgba(60,40,20,.22)",
        }}
      >
        <Img src={spec.src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
    );
  }
  return (
    <div
      style={{
        position: "absolute", left: b.left, top: b.top, width: b.width, height: b.height,
        background: "#f7f0df", border: "1.5px solid rgba(58,50,38,.55)", borderRadius: 8,
        boxShadow: "0 4px 12px rgba(60,40,20,.18)", boxSizing: "border-box", padding: 6,
        overflow: "hidden",
      }}
    >
      {spec.node}
    </div>
  );
};

// 单条槽位渲染（MapPage / MixedPage 共用）
const ItemView: React.FC<{
  it: TextItem; idx: number; total: number;
  b: { left: number; top: number; width: number; height: number };
  photos?: Record<string, PhotoSpec>;
}> = ({ it, idx, total, b, photos }) => {
  const at = 8 + Math.min(idx, 30) * 14 + (it.delay ?? 0);
  if (it.kind === "photo") {
    const spec = photos?.[it.slotId!];
    if (!spec) throw new Error(`${EPISODE}: 槽位 ${it.slotId} 声明为 photo 但页面未提供 PhotoSpec`);
    return (
      <Enter key={idx} at={at}>
        <PhotoSlot spec={spec} b={b} />
      </Enter>
    );
  }
  const style: React.CSSProperties = {
    position: "absolute", left: b.left, top: b.top, width: b.width, height: b.height,
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
  };
  if (it.kind === "tag") {
    // tag 槽贴芯片包围盒（E19Visual 教训：槽远大于芯片 → L6 TAG_SLOT_ALL_WHITE）。
    // mat 铺满整个槽位（inset 0）：芯片居中，槽内不露底图——古地图深色墨迹
    // 不会落进槽边距（L5 的 ink 只含芯片本体），槽位宽＝芯片估宽＋12px。
    const mat = {
      position: "absolute" as const, inset: 0,
      background: "rgba(247,240,223,0.95)", borderRadius: 8,
      boxShadow: "0 2px 8px rgba(60,40,20,0.2)",
      display: "flex", alignItems: "center", justifyContent: "center",
      overflow: "hidden",
    };
    return (
      <Enter key={idx} at={at} y={14} style={{ ...style, overflow: "visible" }}>
        <div style={mat}>
          <div style={{ whiteSpace: "nowrap" }}>
            <EvidenceTag label={it.text} small delay={at} />
          </div>
        </div>
      </Enter>
    );
  }
  if (it.backing) {
    style.background = typeof it.backing === "string" ? String(it.backing) : "rgba(247,240,223,0.95)";
    style.borderRadius = 12;
    style.boxShadow = "0 4px 14px rgba(60,40,20,0.18)";
    style.overflow = "hidden";
    style.boxSizing = "border-box";
    style.padding = (it as { pad?: string }).pad ?? "6px 14px";
  }
  return (
    <Enter key={idx} at={at} y={16} style={style}>
      <FitBlock
        text={it.text}
        boxW={b.width - 28}
        boxH={b.height - 12}
        size={it.size ?? 24}
        color={it.color ?? PALETTE.ink}
        weight={it.weight ?? 700}
        lh={it.lh ?? 1.4}
        align={it.align ?? "center"}
      />
    </Enter>
  );
};

const Items: React.FC<{ page: number; photos?: Record<string, PhotoSpec> }> = ({ page, photos }) => {
  const { cfg, boxOf } = useSlotBoxes(page);
  return (
    <>
      {cfg.items.map((it: TextItem, idx: number) => {
        if (it.kind === "photo" && !it.slotId) return null;
        return (
          <ItemView
            key={idx}
            it={it}
            idx={idx}
            total={cfg.items.length}
            b={boxOf(it.slotId!)}
            photos={photos}
          />
        );
      })}
    </>
  );
};

// 全幅视口页（P3/P6/P8）：页面组件打底（PanZoom/CrossFade/叠合示意），
// overlay 在底图之后、文字槽之前渲染（纸雾渐变等附属层）。
export const MapPage: React.FC<{
  page: number;
  background: React.ReactNode;
  photos?: Record<string, PhotoSpec>;
  overlay?: React.ReactNode;
}> = ({ page, background, photos, overlay }) => (
  <AbsoluteFill>
    {background}
    {overlay}
    <Items page={page} photos={photos} />
  </AbsoluteFill>
);

// 纸底混排页（P1/P2/P4/P5/P7）：PaperBg + 内嵌示意图/装裱真图 + HTML 卡。
// overlay（如 P1 街区索引、P5 演变链）不占槽位，标记类命名一律走 backing tag 槽。
export const MixedPage: React.FC<{
  page: number;
  photos?: Record<string, PhotoSpec>;
  overlay?: React.ReactNode;
}> = ({ page, photos, overlay }) => (
  <AbsoluteFill>
    <PaperBg />
    {overlay}
    <Items page={page} photos={photos} />
  </AbsoluteFill>
);

export { CANVAS, EPISODE };
