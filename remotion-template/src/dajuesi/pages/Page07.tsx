// Page07 — 国保第六批：今日遗存与开放现状。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo: {
        mode: "frame",
        src: staticFile("dajuesi/mec4_composite_eras.png"),
        caption: "大觉寺寺址与旸台山麓空间关系示意 · 制作组示意 · MEC-4",
      },
    }}
  />
);
