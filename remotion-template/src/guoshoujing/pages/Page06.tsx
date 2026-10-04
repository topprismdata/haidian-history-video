// Page06 — 白浮泉引水·全线：线路示意（制作组示意·非测绘拓扑）+ 白浮段书影已上 quote 槽。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo_route: {
        mode: "frame",
        src: staticFile("guoshoujing/guoshoujing_route_mec3.png"),
        caption: "白浮泉—瓮山泊—积水潭引水线路 · 依《元史》原文拓扑 · 制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
