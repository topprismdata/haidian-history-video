// Page03 — E27《白家疃》P03 主图：疃字释义卡（制作组示意）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo_card: {
        mode: "frame",
        src: staticFile("baijiatuan/tuan_ziyi_card.png"),
        caption: "制作组绘制示意 · 非实物照片",
      },
    }}
  />
);
