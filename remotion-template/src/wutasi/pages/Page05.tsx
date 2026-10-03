// Page05 — 断续数十年的一处工程：塔座「累石为台五丈」剖面示意。
import React from "react";
import { MixedPage } from "../SlotPage";

const Terrace: React.FC = () => (
  <svg width={860} height={700} viewBox="0 0 860 700"
       style={{ position: "absolute", left: 970, top: 170 }}>
    {/* 须弥座分层（逐层内收） */}
    <rect x={110} y={520} width={640} height={70} fill="rgba(200,194,180,0.9)" stroke="#787264" strokeWidth={2.5} />
    <rect x={150} y={450} width={560} height={70} fill="rgba(214,208,194,0.9)" stroke="#787264" strokeWidth={2.5} />
    <rect x={195} y={390} width={470} height={60} fill="rgba(222,216,202,0.9)" stroke="#787264" strokeWidth={2.5} />
    {/* 五座密檐小塔 */}
    {[250, 350, 430, 510, 590].map((tx) => (
      <polygon key={tx} points={`${tx - 30},330 ${tx},270 ${tx + 30},330`} fill="rgba(140,100,90,0.75)" />
    ))}
    {/* 券门 */}
    <rect x={405} y={530} width={70} height={58} fill="#3a3630" />
    {/* 石匾位置 */}
    <rect x={390} y={505} width={100} height={22} fill="#a89e8c" stroke="#787264" strokeWidth={2} />
  </svg>
);

export const Page05: React.FC = () => <MixedPage page={5} overlay={<Terrace />} />;
