// Page08 — 岁月留痕：四时代叠合图（MEC-4 纯图形）+ 终局总结卡。
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    overlay={
      <AbsoluteFill style={{ opacity: 0.88, zIndex: 0 }}>
        <Img
          src={staticFile("guajiatun/mec4_composite_eras.png")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    }
  />
);
