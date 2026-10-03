// Page04 — 抄家清单：档案三件套分记 + 二十大罪引文 + 海淀双链方位示意图。
// V-NC01：1793 使团影像未检得 → 本页不冒充使团材料；石舫照片未检得 → 不硬配。
// 方位示意图（node PhotoSpec，kind:"photo" 槽）内纯图形零文字。
import React from "react";
import { MixedPage } from "../SlotPage";

// 海淀双链方位示意（840×420）：西南勺园链（赭虚线）∥ 东北和珅赐园链（青虚线）。
const DualChainMap: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 840 420" preserveAspectRatio="xMidYMid meet">
    <rect x={0} y={0} width={840} height={420} fill="#f4ecd9" />
    {/* 御道与水系 */}
    <path d="M40,300 C240,260 420,280 800,180" stroke="#d8c8a6" strokeWidth={16} fill="none" />
    <path d="M60,340 C260,330 460,300 700,240" stroke="#9db4ae" strokeWidth={10} fill="none" opacity={0.7} />
    <path d="M120,120 C300,160 420,140 560,96" stroke="#9db4ae" strokeWidth={7} fill="none" opacity={0.6} />
    {/* 西南 · 勺园链（弘雅园→集贤院一带） */}
    <ellipse cx={205} cy={260} rx={130} ry={82} fill="none" stroke="#a8452c" strokeWidth={4} strokeDasharray="16 10" />
    <ellipse cx={175} cy={244} rx={40} ry={22} fill="#9db4ae" opacity={0.75} />
    <ellipse cx={242} cy={280} rx={34} ry={19} fill="#9db4ae" opacity={0.75} />
    <rect x={186} y={190} width={44} height={26} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    {/* 东北 · 和珅赐园链（今未名湖一带） */}
    <ellipse cx={620} cy={160} rx={130} ry={76} fill="none" stroke="#2f5d7c" strokeWidth={4} strokeDasharray="16 10" />
    <path d="M560,160 c18,-24 52,-30 74,-12 c20,16 16,42 -6,54 c-26,14 -60,6 -70,-14 c-6,-12 -6,-20 2,-28"
      fill="#9db4ae" stroke="#54788a" strokeWidth={2} />
    <rect x={596} y={106} width={48} height={28} fill="#cdbb92" stroke="#6b5a44" strokeWidth={2} />
    {/* 海淀镇街区（左下示意块） */}
    <g fill="#cdbb92" stroke="#6b5a44" strokeWidth={1.6}>
      <rect x={90} y={330} width={54} height={30} />
      <rect x={158} y={342} width={64} height={32} />
      <rect x={92} y={372} width={70} height={30} />
      <rect x={176} y={384} width={52} height={26} />
    </g>
    {/* 两链分立 · 不相连（四-1 冻结：禁止画成一条接力） */}
    <line x1={335} y1={260} x2={490} y2={160} stroke="#8b7d63" strokeWidth={3} strokeDasharray="4 14" opacity={0.7} />
    <line x1={335} y1={260} x2={490} y2={160} stroke="#f4ecd9" strokeWidth={1.5} strokeDasharray="4 14" />
  </svg>
);

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    photos={{
      p4_map: { mode: "node", node: <DualChainMap /> },
    }}
  />
);
