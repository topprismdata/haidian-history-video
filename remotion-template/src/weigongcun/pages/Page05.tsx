// Page05 — 从「畏吾」到「魏公」：字音与爵位的双重合流。
// 演变链（MEC-4 示意，页面打底不占槽位）：三只虚线圆环节点＋渐进箭头，
// 纯图形零文字——村名一律由链下 backing 文字槽承载。
import React from "react";
import { MixedPage } from "../SlotPage";
import { PALETTE } from "../ui";

// 演变链（1800×250）：畏吾村 → 畏兀村 → 魏公村。
const ChainDiagram: React.FC = () => (
  <svg
    width={1800}
    height={250}
    viewBox="0 0 1800 250"
    style={{ position: "absolute", left: 60, top: 220 }}
  >
    <line x1={470} y1={125} x2={775} y2={125} stroke="#8b7d63" strokeWidth={4} strokeDasharray="15 11" />
    <line x1={1025} y1={125} x2={1330} y2={125} stroke="#8b7d63" strokeWidth={4} strokeDasharray="15 11" />
    <path d="M775,112 l26,13 -26,13 z" fill="#8b7d63" />
    <path d="M1330,112 l26,13 -26,13 z" fill="#8b7d63" />
    <circle cx={350} cy={125} r={95} fill="rgba(47,93,124,0.08)" stroke={PALETTE.indigo} strokeWidth={4} strokeDasharray="18 12" />
    <circle cx={900} cy={125} r={95} fill="rgba(184,134,11,0.08)" stroke={PALETTE.gold} strokeWidth={4} strokeDasharray="18 12" />
    <circle cx={1450} cy={125} r={95} fill="rgba(168,69,44,0.08)" stroke={PALETTE.ochre} strokeWidth={5} strokeDasharray="18 12" />
    <circle cx={350} cy={125} r={56} fill="none" stroke={PALETTE.indigo} strokeWidth={2} opacity={0.55} />
    <circle cx={900} cy={125} r={56} fill="none" stroke={PALETTE.gold} strokeWidth={2} opacity={0.55} />
    <circle cx={1450} cy={125} r={56} fill="none" stroke={PALETTE.ochre} strokeWidth={2} opacity={0.55} />
  </svg>
);

export const Page05: React.FC = () => (
  <MixedPage page={5} overlay={<ChainDiagram />} />
);
