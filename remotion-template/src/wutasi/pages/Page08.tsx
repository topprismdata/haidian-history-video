// Page08 — 三个时间，一方石匾：四时代叠合图。
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    overlay={
      <AbsoluteFill style={{ opacity: 0.88, zIndex: 0 }}>
        <Img
          src={staticFile("wutasi/mec4_composite_eras.png")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    }
  />
);
