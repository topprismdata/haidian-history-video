// Page08 — E27《白家疃》P08 主图：六段时代叠合 + 门额拓影。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    photos={{
      p8_eras: {
        mode: "frame",
        src: staticFile("baijiatuan/mec4_era_overlay.png"),
        caption: "制作组示意 · 非测绘拓扑 · 成村年代存疑（辽金说／明初屯田说两说并存）",
      },
      p8_photo_biane: {
        mode: "frame",
        src: staticFile("baijiatuan/xianwangci_shanmen_biane.png"),
        caption: "制作组绘制 · 非实物扫描 · 据公开著录",
      },
    }}
  />
);
