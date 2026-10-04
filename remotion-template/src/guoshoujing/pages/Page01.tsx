// Page01 — 片头·一泉入都：九龙池干涸龙首 + 收束集钩子。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    photos={{
      p1_photo_gate: {
        mode: "frame",
        src: staticFile("guoshoujing/jiulongchi_dry_schematic.png"),
        caption: "昌平龙山九龙池 · 今日泉眼无自然涌水 · 制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
