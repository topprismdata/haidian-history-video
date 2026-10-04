// Page08 — 收束·他把水留给海淀：终版水脉图（纯 SVG 图形，🔴 不写任何文字——
// E26 教训：SVG 硬编码文字会让负控制误报「判据恒真」；标注一律走 backing 槽）。
// 水脉图走 kind:"photo" 的 node 槽（制作组示意图专用通道，QA 自动排除）。
import React from "react";
import { MixedPage } from "../SlotPage";

const RiverVeins: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 848 744" preserveAspectRatio="xMidYMid meet">
    {/* 主渠：白浮泉—瓮山泊—西水门—积水潭（「西折而南」示意弧线，纯图形，非测绘走向） */}
    <path d="M740,100 C680,130 600,160 540,210 C480,260 440,300 380,340"
          fill="none" stroke="#2f5d7c" strokeWidth={10} strokeLinecap="round" />
    <path d="M380,340 C340,370 320,410 340,450"
          fill="none" stroke="#2f5d7c" strokeWidth={10} strokeLinecap="round" />
    {/* 瓮山泊（先在之湖） */}
    <ellipse cx={320} cy={480} rx={92} ry={54} fill="#bcd0d8" stroke="#2f5d7c" strokeWidth={7} />
    {/* 瓮山泊 → 城内 */}
    <path d="M340,520 C400,570 460,600 520,620"
          fill="none" stroke="#2f5d7c" strokeWidth={10} strokeLinecap="round" />
    {/* 大都城垣（示意） */}
    <rect x={520} y={530} width={290} height={170} rx={16}
          fill="none" stroke="#a8452c" strokeWidth={6} strokeDasharray="14 8" />
    {/* 积水潭 */}
    <ellipse cx={600} cy={590} rx={70} ry={42} fill="#bcd0d8" stroke="#2f5d7c" strokeWidth={7} />
    {/* 出南水门向通州 */}
    <path d="M670,650 C710,676 740,692 790,706"
          fill="none" stroke="#2f5d7c" strokeWidth={10} strokeLinecap="round" />
    {/* 泉眼（白浮泉，干涸＝空心圆） */}
    <circle cx={740} cy={100} r={16} fill="none" stroke="#a8452c" strokeWidth={6} />
    {/* 系列已交付集沿水线的联动节点（纯圆点，无文字） */}
    {[
      [700, 120], [640, 150], [560, 200], [480, 270], [400, 340],
      [340, 480], [440, 580], [600, 590], [740, 690],
    ].map(([cx, cy], i) => (
      <circle key={i} cx={cx} cy={cy} r={9} fill="#a8452c" opacity={0.75} />
    ))}
    {/* 广源闸节点（方形，纯图形） */}
    <rect x={428} y={558} width={24} height={24} fill="#3d6b54" opacity={0.9} />
  </svg>
);

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    photos={{
      p8_photo_veins: {
        mode: "node",
        node: <RiverVeins />,
      },
    }}
  />
);
