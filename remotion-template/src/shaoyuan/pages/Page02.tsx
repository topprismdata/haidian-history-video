// Page02 — 1615：我们看见过勺园。
// ScrollPanView 水平滑移「长卷释读带」：吴彬原卷影像未授权（research.md 九-H1，
// 影像未落盘且 V-NC07 禁生成图补位），本带以同时代文献（A2/A3）释读卷中景致，
// 带内纯图形零文字；全部文献文字落在固定 backing 槽与 tag 槽。
import React from "react";
import { MapPage } from "../SlotPage";
import { ScrollPanView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";

const STRIP_W = 3600;
const STRIP_H = 520;

// 长卷释读带：水系 + 径序节点 + 稻畦（纯 SVG 图形，零文字）。
const PanStrip: React.FC = () => {
  const nodes = [
    [150, 260], [430, 330], [730, 250], [1030, 340], [1330, 260], [1630, 340], [1930, 250],
    [2230, 330], [2530, 260], [2830, 330], [3130, 260], [3400, 300],
  ];
  const path = nodes.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  return (
    <svg width={STRIP_W} height={STRIP_H} viewBox={`0 0 ${STRIP_W} ${STRIP_H}`}>
      <rect x={0} y={0} width={STRIP_W} height={STRIP_H} fill="#f4ecd9" />
      <rect x={0} y={0} width={STRIP_W} height={STRIP_H} fill="none" stroke="#b8a890" strokeWidth={3} />
      <rect x={10} y={10} width={STRIP_W - 20} height={STRIP_H - 20} fill="none" stroke="#d4c8b0" strokeWidth={1.5} />
      {/* 上下装裱绦带 */}
      <rect x={0} y={0} width={STRIP_W} height={26} fill="#8b6f4e" opacity={0.55} />
      <rect x={0} y={STRIP_H - 26} width={STRIP_W} height={26} fill="#8b6f4e" opacity={0.55} />
      {/* 水面缓带 */}
      <path d={path} fill="none" stroke="#9db4ae" strokeWidth={64} strokeLinecap="round" opacity={0.55} />
      <path d={path} fill="none" stroke="#7fa39a" strokeWidth={2.5} strokeDasharray="18 10" />
      {/* 径序节点（风烟里→缨云桥→勺海堂→太乙叶→翠葆楼→林于澨→稻畦） */}
      {nodes.map((p, i) => (
        <g key={i}>
          <circle cx={p[0]} cy={p[1]} r={i % 3 === 0 ? 13 : 9} fill="#f7f0df" stroke="#3a3226" strokeWidth={2.5} />
          <circle cx={p[0]} cy={p[1]} r={3.5} fill="#a8452c" />
        </g>
      ))}
      {/* 桥（缨云桥意象）与舫（定舫意象） */}
      <g stroke="#3a3226" strokeWidth={3} fill="none">
        <path d="M560,352 q45,-52 90,0" />
        <line x1={578} y1={330} x2={572} y2={366} />
        <line x1={632} y1={330} x2={638} y2={366} />
      </g>
      <rect x={1180} y={216} width={110} height={34} fill="#e6d9bd" stroke="#3a3226" strokeWidth={2.5} />
      <path d="M1172,250 l63,-26 63,26" fill="none" stroke="#3a3226" strokeWidth={2.5} />
      {/* 米家灯段：灯形散点 */}
      {[860, 960, 1060].map((x, i) => (
        <g key={i} transform={`translate(${x},${180 + (i % 2) * 46})`}>
          <path d="M0,-26 C14,-16 16,4 0,22 C-16,4 -14,-16 0,-26" fill="#c98a3d" stroke="#8a5a22" strokeWidth={2} opacity={0.85} />
          <line x1={0} y1={-26} x2={0} y2={-38} stroke="#8a5a22" strokeWidth={2} />
        </g>
      ))}
      {/* 稻畦千顷（右端） */}
      <g stroke="#a08a54" strokeWidth={2} opacity={0.8}>
        {Array.from({ length: 10 }).map((_, r) => (
          <line key={r} x1={3560} y1={80 + r * 38} x2={3420} y2={92 + r * 38} />
        ))}
        {Array.from({ length: 5 }).map((_, c) => (
          <line key={`v${c}`} x1={3440 + c * 34} y1={70} x2={3428 + c * 34} y2={430} />
        ))}
      </g>
      {/* 石碑（林于澨意象） */}
      <rect x={2980} y={180} width={26} height={92} rx={5} fill="#ddd0b2" stroke="#3a3226" strokeWidth={2.5} />
    </svg>
  );
};

export const Page02: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[1] * VIDEO.fps);
  return (
    <MapPage
      page={2}
      background={
        <div
          style={{
            position: "absolute", left: 60, top: 120, width: 1800, height: STRIP_H,
            borderRadius: 12, boxShadow: "0 10px 30px rgba(60,40,20,.28)", overflow: "hidden",
          }}
        >
          <ScrollPanView scrollWidth={STRIP_W} viewportWidth={1800} durationInFrames={frames} smooth>
            <PanStrip />
          </ScrollPanView>
        </div>
      }
    />
  );
};

// 供 slots 几何核对：长卷释读带占据 (60,120)-(1860,640)，与槽位表一致。
export const PAGE02_STRIP = { left: 60, top: 120, width: 1800, height: STRIP_H };
export const PAN_STRIP_W = STRIP_W;
