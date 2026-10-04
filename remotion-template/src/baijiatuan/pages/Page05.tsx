// Page05 — E27《白家疃》P05 主图：曹雪芹小道拓扑 + 证据状态红条。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_photo_trail: {
        mode: "frame",
        src: staticFile("baijiatuan/caoxueqin_trail_topology.png"),
        caption: "民间传说与今人命名路线 · 制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
