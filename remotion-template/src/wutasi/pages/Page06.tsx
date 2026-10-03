// Page06 — 五座密檐小塔，四种文字：塔座多语种石刻特写。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page06: React.FC = () => (
  <MixedPage
    page={6}
    photos={{
      p6_photo: {
        mode: "frame",
        src: staticFile("wutasi/wutasi_pagoda_photo.png"),
        caption: "金刚宝座塔与塔座多语种石刻 · VEC-3",
      },
    }}
  />
);
