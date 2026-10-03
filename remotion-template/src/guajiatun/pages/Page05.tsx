// Page05 — 1674 三藩之乱：清圣祖实录吴应熊案书影（VEC-1）+ 抄没转折卡。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_photo: {
        mode: "frame",
        src: staticFile("guajiatun/qingshilu_wuyingxiong_folio.png"),
        caption: "《清圣祖实录·卷四十六》康熙十三年四月吴应熊案书影 · VEC-1",
      },
    }}
  />
);
