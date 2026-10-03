// Page05 — 寺名换了三回：日下旧闻考卷一百六书影（VEC-1）+ 演变链。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_photo: {
        mode: "frame",
        src: staticFile("dajuesi/rixiajiuwenkao_dajuesi_folio.png"),
        caption: "四库全书本《钦定日下旧闻考》卷一百六大觉寺条 · VEC-1",
      },
    }}
  />
);
