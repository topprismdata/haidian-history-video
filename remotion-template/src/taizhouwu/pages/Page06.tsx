// Page06 — 清代印记：黑龙潭与皇家祈雨（政书书影 + 殿宇古建照）
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo: {
        mode: "frame",
        src: staticFile("taizhouwu/heilongtan_longwangmiao_hall.png"),
        caption: "清代黑龙潭龙王庙殿宇遗存 · 康熙敕建祈雨圣地 · VEC-3",
      },
    }}
  />
);
