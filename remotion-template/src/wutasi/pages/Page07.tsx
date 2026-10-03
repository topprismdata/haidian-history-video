// Page07 — 第一批国保：塔与博物馆共存实拍。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo: {
        mode: "frame",
        src: staticFile("wutasi/beijing_1915_changhe_anchor_roi.png"),
        caption: "长河北岸寺院带 · 1915 实测京师四郊图切片 · MEC-2",
      },
    }}
  />
);
