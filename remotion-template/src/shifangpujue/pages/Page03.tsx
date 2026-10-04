// Page03 — 元英宗至治元年，昭孝寺与一尊元代铜佛：铜卧佛全貌。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo_wofoe: {
        mode: "frame",
        src: staticFile("shifangpujue/shifangpujue_wofoe_photo.png"),
        caption: "元代释迦牟尼涅槃铜卧佛 · 长约五米 · VEC-3",
      },
    }}
  />
);
