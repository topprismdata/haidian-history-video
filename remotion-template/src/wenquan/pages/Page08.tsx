// Page08 — 泉去名存：命名链拓扑主 + 地名置换时间轴副。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    photos={{
      p8_photo_chain: {
        mode: "frame",
        src: staticFile("wenquan/mec4_quanming_chain.png"),
        caption: "制作组示意 · 非测绘拓扑",
      },
      p8_photo_timeline: {
        mode: "frame",
        src: staticFile("wenquan/mec3_diming_timeline.png"),
        caption: "制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
