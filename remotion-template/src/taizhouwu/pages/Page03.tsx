// Page03 — 天宝九载：出土墓志的坐标裁判（核心证据页）
// 唐天宝九载焦金府墓志铭拓本书影装裱（Level 1 / VEC-1）+ 裁判卡。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo: {
        mode: "frame",
        src: staticFile("taizhouwu/tang_jiaofujun_epitaph_folio.png"),
        caption: "唐天宝九载《大唐幽州昌平县孤竹府带州故折冲焦府君墓志铭》拓本书影 · Level 1 · VEC-1",
      },
    }}
  />
);
