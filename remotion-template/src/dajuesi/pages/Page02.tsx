// Page02 — 公元 1068：辽碑书影（VEC-1）+ 逐字释文，核心证据页。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo: {
        mode: "frame",
        src: staticFile("dajuesi/liao_qingshuiyuan_stele_folio.png"),
        caption: "辽咸雍四年《旸台山清水院创造藏经记》碑文书影 · 僧志延撰 · VEC-1",
      },
    }}
  />
);
