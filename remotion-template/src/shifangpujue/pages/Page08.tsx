// Page08 — 名字是皇帝给的，佛是元朝铸的：四时代叠合图。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    photos={{
      p8_composite: {
        mode: "frame",
        src: staticFile("shifangpujue/mec4_composite_eras.png"),
        caption: "四时代叠合图 · 制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
