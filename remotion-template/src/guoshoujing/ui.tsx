// ui.tsx — E29《郭守敬·一泉入都》共享视觉语言。
// 从 src/shifangpujue/ui.tsx 复制基础部件（PALETTE/PaperBg/EvidenceTag/Enter/PhotoFrame，
// PhotoFrame 逐字未动 —— 历史影像装裱全片唯一实现，禁止重新设计）。
// E29 调整：证据分级标签色（正史书证 / 行状文集 / 示意图层 / 机构口径）。
import React from "react";
import { AbsoluteFill, Img, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const PALETTE = {
  paper: "#f2e8d5",
  paperDeep: "#e9dcc0",
  ink: "#3a3226",
  inkSoft: "#6b5a44",
  ochre: "#a8452c", // 一手正史 / 实测与遗构 · 赭红
  indigo: "#2f5d7c", // 官书考订 / 文献记载 · 青黛
  legend: "#7c7291", // 示意 / 方位推测层 · 灰紫
  gold: "#b8860b", // 时人记述 / 行状文集 · 金褐
  green: "#3d6b54", // 现行 / 官方口径 · 青绿
};

export const TAG_COLORS: Record<string, string> = {
  // ── 文献层级（沿用系列五级色）──
  文献记载: PALETTE.indigo,
  "官书考订 · 《日下旧闻考》": PALETTE.indigo,
  "转引 E16 直核 · 《日下旧闻考》": PALETTE.indigo,
  "时人记述 · 齐履谦《郭公行状》": PALETTE.gold,
  "行状 · 元人一手": PALETTE.gold,
  "一手正史 · 《元史·郭守敬传》": PALETTE.ochre,
  "一手正史 · 《元史·河渠志》": PALETTE.ochre,
  "正史书证 · 本纪": PALETTE.ochre,
  "正史书证 · 天文志": PALETTE.ochre,
  "现行 · 官方口径": PALETTE.green,
  // ── E29 示意图层 / 判语 ──
  "制作组示意 · 非测绘拓扑": PALETTE.legend,
  "制作组绘制示意 · 非实物照片": PALETTE.legend,
  "衰败链 · 制作组示意": PALETTE.legend,
  "穷举名单排除 · 名单之外无站": PALETTE.legend,
  "一泉入都 · 收束集": PALETTE.ochre,
  "海淀锚点 · 玉泉首想": PALETTE.gold,
  "先有仪表后有历法": PALETTE.indigo,
  "观天在城内 · 引水才经过海淀": PALETTE.green,
  "观天无海淀 · 喝水全靠海淀": PALETTE.green,
  "引水体系 · 白浮泉—瓮山泊—积水潭": PALETTE.indigo,
  "泉死得比人早": PALETTE.ochre,
  "长河先在 · 非郭守敬所开": PALETTE.legend,
  "白浮泉在昌平 · 不在海淀": PALETTE.ochre,
  "据现代学者换算 · 原文无小数": PALETTE.legend,
  "元代实物遗存 · 广源闸": PALETTE.green,
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
