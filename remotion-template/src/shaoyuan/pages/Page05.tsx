// Page05 — 园毁了，物还在说话：物证点位图（MEC-4 node）+ 石舫/石屏双证卡。
// 红线 V-NC05：石屏必须带「移入」徽章；V-NC06：谕旨原文无「石舫」二字的分层表述。
// 点位图标注走 tag 槽（backing 纸垫），SVG 内零文字。
import React from "react";
import { MixedPage } from "../SlotPage";

// 未名湖物证点位示意（900×560）：石舫（原地遗存）/ 石屏（后移入）/ 睿邸山水。
const EvidenceMap: React.FC = () => (
  <svg width="100%" height="100%" viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet">
    <rect x={0} y={0} width={900} height={560} fill="#f4ecd9" />
    <path d="M60,120 C220,80 420,92 620,70" stroke="#d8c8a6" strokeWidth={12} fill="none" />
    {/* 湖体 */}
    <path
      d="M220,320 c30,-80 130,-110 240,-96 c120,14 240,60 300,130 c40,48 20,110 -50,140
         c-90,38 -240,44 -340,16 c-110,-30 -180,-110 -150,-190"
      fill="#a9bdb5" stroke="#54788a" strokeWidth={2.5}
    />
    {/* 湖心岛（石舫所在岛洲意象） */}
    <ellipse cx={560} cy={330} rx={54} ry={30} fill="#e8ddc2" stroke="#6b5a44" strokeWidth={2} />
    {/* 石舫基座（北岸·两说并存示意点位） */}
    <g>
      <rect x={498} y={268} width={64} height={22} fill="#d9c9a4" stroke="#a8452c" strokeWidth={3} />
      <circle cx={530} cy={279} r={7} fill="#a8452c" />
    </g>
    {/* 石屏四扇（东岸·移入） */}
    <g stroke="#2f5d7c" strokeWidth={3}>
      <rect x={742} y={420} width={14} height={58} fill="#d9c9a4" />
      <rect x={762} y={424} width={14} height={58} fill="#d9c9a4" />
      <rect x={782} y={420} width={14} height={58} fill="#d9c9a4" />
      <rect x={802} y={424} width={14} height={58} fill="#d9c9a4" />
    </g>
    <circle cx={780} cy={452} r={8} fill="#2f5d7c" />
    {/* 睿邸山水遗意（南岸） */}
    <path d="M330,540 l40,-38 34,30 28,-40 44,46" fill="none" stroke="#7c7291" strokeWidth={5} strokeLinecap="round" />
    <circle cx={390} cy={536} r={8} fill="#7c7291" />
    {/* 岸线树点 */}
    {[[260, 236], [330, 210], [430, 200], [620, 214], [700, 262], [248, 420], [300, 470], [560, 512]].map(
      (p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={7} fill="#3d6b54" />,
    )}
  </svg>
);

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    overlay={
      <div
        style={{
          position: "absolute", left: 60, top: 140, width: 900, height: 560,
          background: "#f7f0df", border: "1.5px solid rgba(58,50,38,.55)", borderRadius: 8,
          boxShadow: "0 4px 12px rgba(60,40,20,.18)", overflow: "hidden",
        }}
      >
        <EvidenceMap />
      </div>
    }
  />
);
