// ui.tsx — E20《勺园·淑春园·未名湖》共享视觉语言。
// 从 src/cishousi/ui.tsx 复制基础部件（PALETTE/PaperBg/EvidenceTag/Enter/PhotoFrame，
// PhotoFrame 逐字未动 —— 历史影像装裱全片唯一实现，禁止重新设计）。
// E20 新增：档案纪实双轨分级的标签色（MEC 地图证据 / VEC 影像证据 / 文献层级）。
import React from "react";
import { AbsoluteFill, Img, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const PALETTE = {
  paper: "#f2e8d5",
  paperDeep: "#e9dcc0",
  ink: "#3a3226",
  inkSoft: "#6b5a44",
  ochre: "#a8452c", // 一手档案 / 一手谕旨 · 赭红
  indigo: "#2f5d7c", // 文献记载 · 青黛
  legend: "#7c7291", // 示意 / 传闻层 · 灰紫
  gold: "#b8860b", // 时人记述 / 学术争议 · 金褐
  green: "#3d6b54", // 现行 / 现代官方口径 · 青绿
};

export const TAG_COLORS: Record<string, string> = {
  // ── 文献层级（沿用系列五级色）──
  文献记载: PALETTE.indigo,
  官书考订: PALETTE.indigo,
  "官书 · 实录/清史稿 转引": PALETTE.indigo,
  时人记述: PALETTE.gold,
  一手档案: PALETTE.ochre,
  "一手档案 · 转引": PALETTE.ochre,
  "一手谕旨 · 转引《仁宗实录》": PALETTE.ochre,
  一手题跋: PALETTE.ochre,
  "清宗室诗集 · 转引": PALETTE.gold,
  现代研究: PALETTE.green,
  "现代官方口径 · 北大文物页": PALETTE.green,
  "现行 · 官方口径": PALETTE.green,
  "校史考订 · 《燕大月刊》": PALETTE.green,
  "校史考订 · 侯仁之《燕园史话》系统": PALETTE.green,
  "校史转述 · 勺园故址唯一实物线索": PALETTE.green,
  "北大校史馆考订 · 《燕大月刊》": PALETTE.green,
  学术争议: PALETTE.gold,
  "学术争议 · 名称两说并存": PALETTE.gold,
  "谕旨原文无石舫 · 现代引申层": PALETTE.ochre,
  "圆明园夹镜鸣琴移入 · 非和珅园旧物": PALETTE.ochre,
  // ── E20 地图 / 影像证据分级 ──
  "《三山五园图》海淀一带 · MEC-1 清晚期绘本": PALETTE.ochre,
  "研究索引示意 · MEC-4 制作组示意": PALETTE.legend,
  "物证点位 · MEC-4 示意": PALETTE.legend,
  "墨菲总体规划 · 校园格局示意（MEC-4）": PALETTE.legend,
  "和珅赐园在今未名湖一带 · 方位示意（MEC-4）": PALETTE.legend,
  "官书考订 · 今其园不可考": PALETTE.indigo,
  "两园圈 · 方位示意非边界": PALETTE.legend,
  "勺园故址 · 方位示意": PALETTE.legend,
  "和珅赐园 · 方位示意": PALETTE.legend,
  "回忆转述 · 卖主陈树藩": PALETTE.gold,
  "形制参照 · 非图纸依据": PALETTE.gold,
  "原规划图纸未检得注": PALETTE.legend,
  "真图 · 角落小图（出处链待核）": PALETTE.legend,
  "石舫底座 · 原地遗存": PALETTE.ochre,
  "石屏四扇 · 后移入": PALETTE.ochre,
  "睿邸时期 · 山水犹在": PALETTE.gold,
  "1860 重创成废园": PALETTE.indigo,
  // ── E20 点位 / 时代芯片 ──
  未名湖: PALETTE.indigo,
  石舫底座: PALETTE.ochre,
  "勺园故址 · 西南隅一带": PALETTE.legend,
  無名湖: PALETTE.legend,
  睿湖: PALETTE.gold,
  "明代 · 勺园（示意）": PALETTE.legend,
  "清代 · 赐园与水田": PALETTE.ochre,
  "民国 · 燕京大学": PALETTE.indigo,
  "今 · 北京大学燕园": PALETTE.green,
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
        whiteSpace: "nowrap",
      }}
    >
      [{label}]
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

// ── PhotoFrame：历史影像统一装裱框（2026-10-03 用户定，全片唯一实现）──
// 卡纸+双线内框+来源条常显，object-fit:contain 永不裁切真图；
// 禁加颗粒/银盐边框/做旧相纸（伪造「原件即如此」）。
export const PhotoFrame: React.FC<{
  src: string; caption: string; width: number; height: number;
  left?: number; top?: number;
}> = ({ src, caption, width, height, left, top }) => {
  const pad = width >= 1200 ? 24 : width >= 700 ? 24 : width >= 460 ? 20 : 16;
  return (
    <div
      style={{
        position: "absolute",
        left: left ?? (1920 - width) / 2,
        top: top ?? 110,
        width,
        height: height + pad * 2 + 34,
        background: "#f7f0df",
        borderRadius: 10,
        boxShadow: "0 6px 18px rgba(60,40,20,.22)",
        boxSizing: "border-box",
        padding: pad,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          position: "relative",
          width: "100%",
          height,
          background: "#f7f0df",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Img
          src={src}
          style={{
            maxWidth: "100%",
            maxHeight: "100%",
            objectFit: "contain",
            border: "1.5px solid rgba(58,50,38,.55)",
            boxShadow: "inset 0 0 0 4px #f7f0df, inset 0 0 0 5px rgba(58,50,38,.35)",
            background: "#f7f0df",
          }}
        />
      </div>
      <div
        style={{
          marginTop: 10,
          fontSize: 14,
          lineHeight: "20px",
          color: "#5a4f3c",
          fontWeight: 700,
          textAlign: "center",
          letterSpacing: 0.3,
        }}
      >
        {caption}
      </div>
    </div>
  );
};
