// Page07 — 一面山壁，三层字：水流云在摩崖示意主 + 滦州纪念塔示意副。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo_shuiliu: {
        mode: "frame",
        src: staticFile("wenquan/shuiliu_yunzai_moyai.png"),
        caption: "制作组绘制示意 · 非实物照片 · 字体排印非手迹",
      },
      p7_photo_luanzhou: {
        mode: "frame",
        src: staticFile("wenquan/luanzhou_jinianta.png"),
        caption: "制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
