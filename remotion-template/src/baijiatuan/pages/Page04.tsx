// Page04 — E27《白家疃》P04 主图：怡贤亲王祠残碑碑额拓影。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    photos={{
      p4_photo_beibi: {
        mode: "frame",
        src: staticFile("baijiatuan/xianwangci_beiji_tuoying.png"),
        caption: "制作组绘制 · 非原石拓片 · 据公开著录",
      },
    }}
  />
);
