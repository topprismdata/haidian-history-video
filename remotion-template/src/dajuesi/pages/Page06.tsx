// Page06 — 三废三兴：御书四额与殿宇实拍。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo: {
        mode: "frame",
        src: staticFile("dajuesi/dajuesi_hall_photo.png"),
        caption: "大觉寺无量寿佛殿 · 额曰动静等观 · VEC-3",
      },
    }}
  />
);
