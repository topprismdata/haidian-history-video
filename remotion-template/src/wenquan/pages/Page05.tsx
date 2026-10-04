// Page05 — 一冷一热：黑龙潭龙王庙示意主；祈/浴功能对置由两卡槽位承担。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_photo_hlt: {
        mode: "frame",
        src: staticFile("wenquan/heilongtan_longwangmiao.png"),
        caption: "制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
