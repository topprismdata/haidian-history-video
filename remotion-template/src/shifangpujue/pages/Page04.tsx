// Page04 — 寺是唐的，佛是元的：年代错位核心页。
//
// 🔴 E26 教训：负控制只认 slots.json 里的槽位。**SVG 覆盖层内的硬编码文字
//    不在槽位体系内**，负控制平移落点会罩住那些字并误判「判据恒真」。
//    因此本页 AgeGapBar 改为**纯图形**（零文字），所有文字一律走槽位：
//    p4_axis_era_left / p4_axis_era_right / p4_axis_gap。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

const AgeGapBar: React.FC = () => (
  <svg width={860} height={120} viewBox="0 0 860 120"
       style={{ position: "absolute", left: 60, top: 806 }}>
    <line x1={40} y1={40} x2={820} y2={40} stroke="#8a7c62" strokeWidth={6} />
    {/* 寺（唐） */}
    <circle cx={70} cy={40} r={13} fill="#a8452c" />
    <circle cx={790} cy={40} r={13} fill="#5a6b8a" />
    {/* 间隔区间的淡色带（纯图形，无文字） */}
    <rect x={96} y={28} width={680} height={24} fill="#c8b48a" opacity={0.35} />
  </svg>
);

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    overlay={<AgeGapBar />}
    photos={{
      p4_photo_face: {
        mode: "frame",
        src: staticFile("shifangpujue/shifangpujue_wofoe_face.png"),
        caption: "铜卧佛面部 · 制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
