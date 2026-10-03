// Page01 — 背对太阳的古刹：旸台山麓索引示意（MEC-4）+ 大觉寺实拍镜框。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const FoothillIndex: React.FC = () => (
  <svg width={860} height={460} viewBox="0 0 860 460"
       style={{ position: "absolute", left: 60, top: 240 }}>
    {/* 旸台山山脊（西北高、东南低） */}
    <path d="M0,60 Q240,10 520,90 T860,150 L860,0 L0,0 Z"
          fill="rgba(107,90,68,0.10)" stroke="#6b5a44" strokeWidth={2.5} strokeDasharray="8 5" />
    {/* 御道 */}
    <line x1={0} y1={360} x2={860} y2={330} stroke="#d8c8a6" strokeWidth={14} />
    <line x1={0} y1={360} x2={860} y2={330} stroke="#f7f0df" strokeWidth={2} strokeDasharray="12 9" />
    {/* 大觉寺方位圈（旸台山南麓） */}
    <circle cx={420} cy={200} r={50} fill="rgba(168,69,44,0.08)" stroke="#a8452c" strokeWidth={3} strokeDasharray="8 6" />
    {/* 西向箭头（坐西朝东的反向：寺面西） */}
    <path d="M420,200 L330,200" stroke="#a8452c" strokeWidth={3.5} markerEnd="" />
    <path d="M330,200 L346,192 L346,208 Z" fill="#a8452c" />
    {/* 黑龙潭 */}
    <circle cx={620} cy={270} r={28} fill="rgba(47,93,124,0.12)" stroke="#2f5d7c" strokeWidth={2.5} />
    {/* 北安河村 */}
    <rect x={180} y={318} width={40} height={28} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<FoothillIndex />}
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("dajuesi/dajuesi_hall_photo.png"),
        caption: "大觉寺无量寿佛殿（额曰动静等观）· VEC-3",
      },
    }}
  />
);
