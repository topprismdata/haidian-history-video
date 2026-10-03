// Page01 — 今天的太舟坞：海淀西北山水街区索引（MEC-4，页面打底不占槽位）
// + 现代太舟坞/西山实景镜框。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const StreetIndex: React.FC = () => (
  <svg
    width={860}
    height={480}
    viewBox="0 0 860 480"
    style={{ position: "absolute", left: 60, top: 220 }}
  >
    {/* 西山山脉轮廓 */}
    <path
      d="M0,180 Q180,60 380,140 T760,80 L860,120 L860,0 L0,0 Z"
      fill="rgba(107, 90, 68, 0.08)"
      stroke="#6b5a44"
      strokeWidth={2}
      strokeDasharray="6 4"
    />
    {/* 京密引水渠水网 */}
    <path
      d="M40,380 C260,340 500,280 840,240"
      stroke="#2f5d7c"
      strokeWidth={14}
      fill="none"
      opacity={0.8}
    />
    {/* 温泉路 / 现代道路 */}
    <rect x={140} y={160} width={20} height={320} fill="#d8c8a6" />
    <line x1={150} y1={160} x2={150} y2={480} stroke="#f7f0df" strokeWidth={2} strokeDasharray="10 8" />
    <line x1={40} y1={310} x2={840} y2={310} stroke="#d8c8a6" strokeWidth={16} />
    {/* 太舟坞古村落方位圈 */}
    <circle cx={460} cy={310} r={56} fill="rgba(168,69,44,0.08)" stroke="#a8452c" strokeWidth={3} strokeDasharray="8 6" />
    {/* 黑龙潭泉眼位 */}
    <circle cx={280} cy={220} r={36} fill="rgba(47,93,124,0.12)" stroke="#2f5d7c" strokeWidth={3} />
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<StreetIndex />}
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("taizhouwu/modern_taizhouwu_street.png"),
        caption: "现代海淀温泉镇太舟坞街区与西山远眺 · Wikimedia Commons · VEC-2",
      },
    }}
  />
);
