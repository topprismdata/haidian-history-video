// Page02 — 宋辽烟云：宋史杨延昭传书影（VEC-1）+ 地理辨伪卡。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo: {
        mode: "frame",
        src: staticFile("guajiatun/songshi_yangyanzhao_folio.png"),
        caption: "百衲本《宋史·卷二百七十二·杨延昭传》原刊书影 · VEC-1",
      },
    }}
  />
);
