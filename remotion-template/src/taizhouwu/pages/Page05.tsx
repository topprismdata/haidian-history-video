// Page05 — 何谓「太舟坞」？水文与船坞的真相（水利解构 + 双轨假说）
import React from "react";
import { MixedPage } from "../SlotPage";

// 船坞水利结构示意图（页面打底内嵌，无文字）
const WharfDiagram: React.FC = () => (
  <svg
    width={860}
    height={400}
    viewBox="0 0 860 400"
    style={{ position: "absolute", left: 60, top: 460 }}
  >
    {/* 山麓坡面 */}
    <path d="M0,0 L200,200 L0,400 Z" fill="rgba(107, 90, 68, 0.08)" stroke="#6b5a44" strokeWidth={2} />
    {/* 运石水渠主航道 */}
    <rect x={160} y={120} width={700} height={160} fill="#2f5d7c" opacity={0.2} rx={6} />
    {/* 凹入泊船官坞 (U形港) */}
    <path
      d="M320,120 L320,320 L580,320 L580,120 Z"
      fill="#2f5d7c"
      opacity={0.35}
      stroke="#2f5d7c"
      strokeWidth={3}
    />
    {/* 装卸条石栈道与吊装台架 */}
    <line x1={320} y1={280} x2={220} y2={280} stroke="#a8452c" strokeWidth={6} strokeDasharray="12 8" />
    <rect x={360} y={160} width={180} height={100} fill="#f7f0df" stroke="#a8452c" strokeWidth={3} rx={4} />
  </svg>
);

export const Page05: React.FC = () => (
  <MixedPage page={5} overlay={<WharfDiagram />} />
);
