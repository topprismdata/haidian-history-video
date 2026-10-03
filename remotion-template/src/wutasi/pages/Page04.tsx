// Page04 — 永乐初年：西域僧人与印度图样（金刚宝座式源流示意）。
import React from "react";
import { MixedPage } from "../SlotPage";

const StyleOrigin: React.FC = () => (
  <svg width={860} height={680} viewBox="0 0 860 680"
       style={{ position: "absolute", left: 970, top: 180 }}>
    {/* 左：印度佛陀迦耶精舍（大菩提寺）式样 */}
    <rect x={60} y={180} width={200} height={200} fill="rgba(200,170,110,0.20)" stroke="#a8842e" strokeWidth={3} />
    <polygon points={(60,180),(160,90),(260,180)} fill="rgba(200,170,110,0.32)" stroke="#a8842e" strokeWidth={2} />
    {/* 五塔抽象 */}
    <polygon points={(110,150),(120,120),(130,150)} fill="#a8842e" />
    <polygon points={(150,150),(160,110),(170,150)} fill="#a8842e" />
    <polygon points={(190,150),(200,112),(210,150)} fill="#a8842e" />

    {/* 箭头 */}
    <line x1={300} y1={280} x2={500} y2={280} stroke="#a8452c" strokeWidth={4} />
    <polygon points={(500,280),(480,268),(480,292)} fill="#a8452c" />

    {/* 右：明真觉寺金剛寶座塔 */}
    <rect x={540} y={220} width={200} height={160} fill="rgba(168,69,44,0.16)" stroke="#a8452c" strokeWidth={3} />
    <polygon points={(600,220),(640,130),(680,220)} fill="rgba(168,69,44,0.55)" />
    <polygon points={(560,220),(590,160),(620,220)} fill="rgba(168,69,44,0.45)" />
    <polygon points={(660,220),(690,160),(720,220)} fill="rgba(168,69,44,0.45)" />

    {/* 塔座密檐线 */}
    <line x1={540} y1={330} x2={740} y2={330} stroke="#a8452c" strokeWidth={2} />
    <line x1={540} y1={350} x2={740} y2={350} stroke="#a8452c" strokeWidth={2} />
  </svg>
);

export const Page04: React.FC = () => <MixedPage page={4} overlay={<StyleOrigin />} />;
