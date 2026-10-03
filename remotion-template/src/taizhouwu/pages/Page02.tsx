// Page02 — 公元 705：唐中宗的羁縻「带州」
// 四库全书本《旧唐书·地理志二》原刊书影装裱（VEC-1）+ 羁縻政区卡。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo: {
        mode: "frame",
        src: staticFile("taizhouwu/tang_daizhou_jiu_tangshu_folio.png"),
        caption: "《旧唐书·卷三十九·地理志二》带州条目书影 · 文渊阁四库全书本 · VEC-1",
      },
    }}
  />
);
