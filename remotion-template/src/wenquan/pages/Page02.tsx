// Page02 — 明末文献里的第一眼温泉：《帝京景物略》书影主 + 甃池剖面示意副。
// 剖面为纯图形（零文字）——所有文字一律走槽位，SVG 不得硬编码文字。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const ZhouProfile: React.FC = () => (
  <svg width={560} height={240} viewBox="0 0 560 240">
    {/* 地面线 */}
    <line x1={20} y1={60} x2={540} y2={60} stroke="#8a7c62" strokeWidth={4} />
    {/* 地层剖面 */}
    <rect x={20} y={60} width={520} height={160} fill="#d9cdb0" opacity={0.55} />
    {/* 甃砖池壁（左右） */}
    {[0, 1, 2, 3, 4].map((i) => (
      <rect key={"l" + i} x={150} y={80 + i * 26} width={26} height={22} fill="#a8967a" stroke="#6b5a44" strokeWidth={1.5} />
    ))}
    {[0, 1, 2, 3, 4].map((i) => (
      <rect key={"r" + i} x={384} y={80 + i * 26} width={26} height={22} fill="#a8967a" stroke="#6b5a44" strokeWidth={1.5} />
    ))}
    {/* 池底 */}
    <rect x={150} y={212} width={260} height={22} fill="#a8967a" stroke="#6b5a44" strokeWidth={1.5} />
    {/* 温泉水体（微沸波纹） */}
    <rect x={178} y={150} width={204} height={60} fill="#7fa8b8" opacity={0.75} />
    <path d="M196,142 q10,-9 20,0 t20,0 t20,0 t20,0 t20,0 t20,0 t20,0 t20,0 t20,0" fill="none" stroke="#5d8a9c" strokeWidth={3} />
    {/* 泉眼上涌气泡 */}
    <circle cx={252} cy={196} r={5} fill="#d7e6ec" />
    <circle cx={286} cy={184} r={4} fill="#d7e6ec" />
    <circle cx={318} cy={198} r={6} fill="#d7e6ec" />
    {/* 热气（图形曲线） */}
    <path d="M240,52 q8,-16 0,-30 q-8,-14 0,-26" fill="none" stroke="#b8a98c" strokeWidth={3} opacity={0.8} />
    <path d="M286,52 q8,-16 0,-30 q-8,-14 0,-26" fill="none" stroke="#b8a98c" strokeWidth={3} opacity={0.65} />
    <path d="M330,52 q8,-16 0,-30 q-8,-14 0,-26" fill="none" stroke="#b8a98c" strokeWidth={3} opacity={0.8} />
  </svg>
);

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo_folio: {
        mode: "frame",
        src: staticFile("wenquan/dijing_jingwulue_folio.png"),
        caption: "《帝京景物略》「温泉」条 · 依公开文本排印 · 非原刊扫描",
      },
      p2_photo_zhou: { mode: "node", node: <ZhouProfile /> },
    }}
  />
);
