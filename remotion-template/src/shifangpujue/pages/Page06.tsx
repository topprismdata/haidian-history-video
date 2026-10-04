// Page06 — 清雍正十二年，赐名十方普觉寺：寺额拓影。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo_banner: {
        mode: "frame",
        src: staticFile("shifangpujue/shie_yaodian_tuoying.png"),
        caption: "寺额「十方普觉寺」· 排印示意 · 非实物拓片",
      },
    }}
  />
);
