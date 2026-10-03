// Page06 — 1920s：废园变大学：1926 校园全景真图 + 墨菲规划示意（node）
// + 1860 通州燃灯塔对照真图。V-NC02：燃灯塔照片只作「形制参照」；
// 墨菲原图纸未检得 → 校园格局为制作组示意（MEC-4），注记槽明示非测绘图。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

// 校园格局示意（880×240）：湖区 + 建筑带 + 中轴 + 塔址（纯图形零文字）。
const CampusPlan: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 880 240" preserveAspectRatio="xMidYMid meet">
    <rect x={0} y={0} width={880} height={240} fill="#f4ecd9" />
    <path d="M40,150 C240,120 460,130 660,110" stroke="#d8c8a6" strokeWidth={10} fill="none" />
    {/* 中轴 */}
    <line x1={120} y1={196} x2={700} y2={92} stroke="#b8a888" strokeWidth={3} strokeDasharray="10 8" />
    {/* 湖区 */}
    <path
      d="M420,120 c26,-44 96,-56 160,-44 c64,12 120,40 140,76 c14,28 -10,52 -58,62
         c-70,14 -160,10 -212,-12 c-46,-20 -52,-56 -30,-82"
      fill="#a9bdb5" stroke="#54788a" strokeWidth={2}
    />
    <ellipse cx={560} cy={128} rx={26} ry={13} fill="#e8ddc2" stroke="#6b5a44" strokeWidth={1.5} />
    {/* 建筑带（中西合璧：殿式屋顶列阵） */}
    <g fill="#cdbb92" stroke="#6b5a44" strokeWidth={1.8}>
      <path d="M180,168 l26,-14 26,14 z" />
      <rect x={184} y={168} width={44} height={20} />
      <path d="M260,158 l28,-15 28,15 z" />
      <rect x={264} y={158} width={48} height={22} />
      <path d="M345,148 l28,-15 28,15 z" />
      <rect x={349} y={148} width={48} height={22} />
      <path d="M690,84 l30,-16 30,16 z" />
      <rect x={694} y={84} width={52} height={24} />
      <path d="M770,96 l26,-14 26,14 z" />
      <rect x={774} y={96} width={44} height={20} />
    </g>
    {/* 塔址（东南，水塔） */}
    <circle cx={836} cy={186} r={20} fill="none" stroke="#6b5a44" strokeWidth={3} />
    <path d="M829,196 l7,-22 7,22" fill="none" stroke="#6b5a44" strokeWidth={2.5} />
    {/* 树点 */}
    {[[150, 120], [230, 96], [330, 84], [520, 60], [640, 52], [760, 60], [120, 210], [350, 214]].map(
      (p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={6} fill="#3d6b54" />,
    )}
  </svg>
);

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo1: {
        mode: "frame",
        src: staticFile("shaoyuan/commons_2016_shibao_stele.jpg"),
        caption: "燕京大学校园远眺西山 · 1926 · Wikimedia Commons · VEC-2",
      },
      p6_plan: { mode: "node", node: <CampusPlan /> },
      p6_photo2: {
        mode: "frame",
        src: staticFile("shaoyuan/commons_2017_boya_lake.jpg"),
        caption: "通州燃灯塔 · 1860 年照片 · Wikimedia Commons · VEC-3",
      },
    }}
  />
);
