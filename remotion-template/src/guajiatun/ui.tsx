// ui.tsx — E21《魏公村·高梁河畔的畏吾村》共享视觉语言。
// 从 src/shaoyuan/ui.tsx 复制基础部件（PALETTE/PaperBg/EvidenceTag/Enter/PhotoFrame，
// PhotoFrame 逐字未动 —— 历史影像装裱全片唯一实现，禁止重新设计）。
// E21 调整：档案纪实双轨分级的标签色（MEC 地图证据 / VEC 影像证据 / 文献层级）。
import React from "react";
import { AbsoluteFill, Img, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const PALETTE = {
  paper: "#f2e8d5",
  paperDeep: "#e9dcc0",
  ink: "#3a3226",
  inkSoft: "#6b5a44",
  ochre: "#a8452c", // 一手档案 / 正史书证 / 实测地图 · 赭红
  indigo: "#2f5d7c", // 文献记载 / 官书考订 · 青黛
  legend: "#7c7291", // 示意 / 方位推测层 · 灰紫
  gold: "#b8860b", // 时人记述 / 文集书证 · 金褐
  green: "#3d6b54", // 现行 / 官方口径 · 青绿
};

export const TAG_COLORS: Record<string, string> = {
  // ── 文献层级（沿用系列五级色）──
  文献记载: PALETTE.indigo,
  "文献记载 · 清人考据": PALETTE.indigo,
  "文献记载 · 清人札记": PALETTE.indigo,
  官书考订: PALETTE.indigo,
  "官书考订 · 《日下旧闻考》卷九十八": PALETTE.indigo,
  时人记述: PALETTE.gold,
  "文集书证 · 李东阳《怀麓堂集》": PALETTE.gold,
  一手档案: PALETTE.ochre,
  "正史列传 · 元史卷一百二十六": PALETTE.ochre,
  "一手书证 · 《元史·廉希宪传》": PALETTE.ochre,
  "神道碑 · 元明善撰": PALETTE.ochre,
  现代研究: PALETTE.green,
  "现行 · 官方口径": PALETTE.green,
  "全国重点文物保护单位 · 编号5-199": PALETTE.green,
  // ── E21 地图 / 影像证据分级 ──
  "《三山五园图》高梁河一带 · MEC-1": PALETTE.ochre,
  "民国档案 · 北洋陆军测地局《实测京师四郊图》": PALETTE.ochre,
  "一手实测档案 · 测绘定型": PALETTE.ochre,
  "演变脉络 · MEC-4 制作组示意": PALETTE.legend,
  "现代街区索引 · MEC-4 制作组示意": PALETTE.legend,
  "四时代叠合 · MEC-4 制作组示意 · 非测绘拓扑": PALETTE.legend,
  "高梁河（今南长河）水道": PALETTE.indigo,
  "畏吾村故址 · 方位示意": PALETTE.legend,
  "南北大道 · 今中关村南大街一带": PALETTE.legend,
  "正史刊本书影 · VEC-1": PALETTE.ochre,
  "建校初期影像 · VEC-2": PALETTE.gold,
  // ── E21 演变轨道 / 时代芯片 ──
  "音转 · 语言层": PALETTE.legend,
  "爵位 · 史册层": PALETTE.ochre,
  "建校档案 · 中央民族学院": PALETTE.green,
  "空间相逢 · 从畏吾村到民族大学": PALETTE.green,
  魏公村地铁站: PALETTE.indigo,
  中央民族大学: PALETTE.indigo,
  国家图书馆: PALETTE.indigo,
  "元 · 畏吾村墓原": PALETTE.ochre,
  "明 · 佛刹与村落": PALETTE.gold,
  "清 · 长河水道": PALETTE.indigo,
  "今 · 高校街区": PALETTE.green,
  "魏公村 · 1915 定名": PALETTE.ochre,
  "大慧寺 · 明代古刹": PALETTE.gold,
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
