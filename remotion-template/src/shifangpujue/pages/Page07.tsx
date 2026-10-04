// Page07 — 第五批国保：寺在国家植物园里。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo_garden: {
        mode: "frame",
        src: staticFile("shifangpujue/shifangpujue_garden_view.png"),
        caption: "卧佛寺与国家植物园共存实景 · VEC-3",
      },
    }}
  />
);
