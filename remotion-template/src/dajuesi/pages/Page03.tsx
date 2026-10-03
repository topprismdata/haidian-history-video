// Page03 — 金章宗的八院是明人写下的：帝京景物略书影 + 时序对照。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo: {
        mode: "frame",
        src: staticFile("dajuesi/dijingjingwulue_folio.png"),
        caption: "《帝京景物略》卷五大觉寺条原刊书影 · VEC-1",
      },
    }}
  />
);
