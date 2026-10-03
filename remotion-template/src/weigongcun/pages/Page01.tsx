// Page01 — 今天的魏公村：现代街区索引示意（MEC-4，页面打底不占槽位）
// + 民大东门实拍镜框。虚线椭圆＝畏吾村故址方位（非边界复原图）；
// 索引图内零文字（命名一律走 backing tag 槽）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

// 现代街区索引（900×600）：西三环 ∥ 中关村南大街双轴 + 长河 + 高校块面。
const StreetIndex: React.FC = () => (
  <svg
    width={900}
    height={600}
    viewBox="0 0 900 600"
    style={{ position: "absolute", left: 60, top: 240 }}
  >
    {/* 南长河（今长河） */}
    <path d="M0,88 C230,64 440,102 900,70" stroke="#9db4ae" strokeWidth={14} fill="none" opacity={0.85} />
    {/* 西三环（西）与中关村南大街（东） */}
    <rect x={108} y={0} width={24} height={600} fill="#d8c8a6" />
    <line x1={120} y1={0} x2={120} y2={600} stroke="#f7f0df" strokeWidth={2.5} strokeDasharray="18 14" />
    <rect x={690} y={0} width={26} height={600} fill="#d8c8a6" />
    <line x1={703} y1={0} x2={703} y2={600} stroke="#f7f0df" strokeWidth={2.5} strokeDasharray="18 14" />
    {/* 畏吾村故址方位（虚线椭圆 · 非边界） */}
    <ellipse cx={560} cy={385} rx={195} ry={132} fill="rgba(168,69,44,0.06)"
      stroke="#a8452c" strokeWidth={3.5} strokeDasharray="16 11" />
    {/* 高校块面 */}
    <g fill="#cdbb92" stroke="#6b5a44" strokeWidth={2}>
      <rect x={430} y={128} width={230} height={110} />
      <rect x={440} y={300} width={230} height={160} />
      <rect x={742} y={300} width={120} height={110} />
      <rect x={450} y={505} width={220} height={85} />
    </g>
    {/* 民大东门（中关村南大街西侧门钉） */}
    <rect x={660} y={366} width={16} height={34} fill="#a8452c" opacity={0.8} />
    {/* 魏公村地铁站 */}
    <circle cx={703} cy={450} r={20} fill="none" stroke="#2f5d7c" strokeWidth={3} strokeDasharray="7 6" />
    <circle cx={703} cy={450} r={12} fill="#2f5d7c" stroke="#f7f0df" strokeWidth={3} />
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<StreetIndex />}
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("weigongcun/modern_weigongcun_street.png"),
        caption: "中央民族大学东门与魏公村街区今貌 · 2017 · Wikimedia Commons · CC BY-SA 4.0 · VEC-2",
      },
    }}
  />
);
