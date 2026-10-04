// Page03 — 测天之前·先造仪器：简仪示意（明仿制标注，原件不存）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo_jianyi: {
        mode: "frame",
        src: staticFile("guoshoujing/jianyi_schematic.png"),
        caption: "简仪结构示意 · 原件不存，明仿制品今存南京 · 制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
