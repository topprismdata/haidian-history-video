// Page01 — 一座寺，五个名字：寿安山南麓索引示意 + 山门实拍。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const ShuoanIndex: React.FC = () => (
  <svg width={860} height={460} viewBox="0 0 860 460"
       style={{ position: "absolute", left: 60, top: 700 }}>
    {/* 三山（寿安山居中，香山/玉泉山为不同山名，V-NC05） */}
    <path d="M60,180 L220,80 L380,180 Z" fill="#8f9a86" opacity={0.75} />
    <path d="M330,190 L520,70 L710,190 Z" fill="#7d8a78" opacity={0.85} />
    <path d="M600,200 L740,110 L860,200 Z" fill="#8f9a86" opacity={0.7} />
    {/* 寿安山（十方普觉寺所在，非香山） */}
    <circle cx={520} cy={130} r={54} fill="rgba(168,69,44,0.08)"
            stroke="#a8452c" strokeWidth={3} strokeDasharray="8 6" />
    <rect x={504} y={96} width={32} height={54} fill="#a8452c" opacity={0.85} />
    {/* 山名标注 */}
    <text x={430} y={222} fontSize={22} fill="#4a4236" textAnchor="middle">香山</text>
    <text x={520} y={262} fontSize={24} fill="#a8452c" textAnchor="middle" fontWeight={700}>寿安山</text>
    <text x={700} y={240} fontSize={22} fill="#4a4236" textAnchor="middle">玉泉山</text>
    {/* 寿安山南麓 */}
    <rect x={430} y={286} width={180} height={112} fill="rgba(120,148,96,0.14)"
          stroke="#6b8a5a" strokeWidth={2} strokeDasharray="6 5" />
    <text x={520} y={424} fontSize={20} fill="#5a6b4a" textAnchor="middle">寿安山南麓 · 今国家植物园</text>
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<ShuoanIndex />}
    photos={{
      p1_photo_gate: {
        mode: "frame",
        src: staticFile("shifangpujue/shifangpujue_garden_view.png"),
        caption: "卧佛寺山门实景 · 寿安山南麓 · VEC-3",
      },
    }}
  />
);
