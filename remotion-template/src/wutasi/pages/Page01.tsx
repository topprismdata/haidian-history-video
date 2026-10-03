// Page01 — 塔上的匾写的是塔的名字：长河北岸索引示意 + 券门石匾特写。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const ChangheIndex: React.FC = () => (
  <svg width={860} height={460} viewBox="0 0 860 460"
       style={{ position: "absolute", left: 60, top: 240 }}>
    {/* 长河（东西向水流） */}
    <path d="M0,330 C220,300 460,340 860,290" stroke="#2f5d7c" strokeWidth={22} fill="none" opacity={0.8} />
    {/* 白石桥 */}
    <rect x={200} y={300} width={16} height={90} fill="#d8c8a6" stroke="#6b5a44" strokeWidth={2} />
    {/* 金刚宝座塔方位 */}
    <rect x={300} y={230} width={40} height={70} fill="#a8452c" opacity={0.85} />
    <circle cx={320} cy={210} r={44} fill="rgba(168,69,44,0.08)" stroke="#a8452c" strokeWidth={3} strokeDasharray="8 6" />
    {/* 五塔寺村 */}
    <rect x={560} y={200} width={130} height={80} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    {/* 西直门方位 */}
    <rect x={790} y={150} width={50} height={130} fill="#d8c8a6" stroke="#6b5a44" strokeWidth={2} />
  </svg>
);

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    overlay={<ChangheIndex />}
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("wutasi/quanmen_shibei_folio.png"),
        caption: "券门石匾特写 · 一手实物 · VEC-1",
      },
    }}
  />
);
