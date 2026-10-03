// Page01 — 挂甲屯现貌：万泉河水系索引示意（MEC-4，页面打底不占槽位）
// + 挂甲屯社区实拍镜框。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const StreetIndex: React.FC = () => (
  <svg
    width={860}
    height={480}
    viewBox="0 0 860 480"
    style={{ position: "absolute", left: 60, top: 230 }}
  >
    {/* 万泉河水系 */}
    <path
      d="M0,400 C200,370 420,400 640,340 C760,310 820,300 860,300"
      stroke="#2f5d7c"
      strokeWidth={16}
      fill="none"
      opacity={0.8}
    />
    {/* 万泉河路 */}
    <line x1={0} y1={430} x2={860} y2={430} stroke="#d8c8a6" strokeWidth={14} />
    <line x1={0} y1={430} x2={860} y2={430} stroke="#f7f0df" strokeWidth={2} strokeDasharray="10 8" />
    {/* 挂甲屯古村方位圈 */}
    <circle cx={420} cy={360} r={54} fill="rgba(168,69,44,0.08)" stroke="#a8452c" strokeWidth={3} strokeDasharray="8 6" />
    {/* 亮甲店（杨家将传说带邻村） */}
    <circle cx={180} cy={386} r={26} fill="rgba(107,90,68,0.10)" stroke="#6b5a44" strokeWidth={2.5} strokeDasharray="6 5" />
    {/* 御园西墙 */}
    <rect x={600} y={140} width={10} height={220} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    <rect x={730} y={110} width={90} height={90} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<StreetIndex />}
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("guajiatun/modern_guajiatun_street.png"),
        caption: "挂甲屯社区今貌 · 2020 · VEC-2",
      },
    }}
  />
);
