// Page03 — 比书更早的石头：地名置换时间轴主（无书证段虚线）+ 采石题记摩崖副。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo_timeline: {
        mode: "frame",
        src: staticFile("wenquan/mec3_diming_timeline.png"),
        caption: "制作组示意 · 非测绘拓扑",
      },
      p3_photo_caishi: {
        mode: "frame",
        src: staticFile("wenquan/caishi_moyai_shiyi.png"),
        caption: "制作组绘制示意 · 非实物照片 · 刻痕非释文",
      },
    }}
  />
);
