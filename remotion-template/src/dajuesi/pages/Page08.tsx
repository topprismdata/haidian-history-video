// Page08 — 一座寺，两个名字，三次重生：四时代叠合图（MEC-4）+ 终局立意。
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page08: React.FC = () => (
  <MixedPage
    page={8}
    overlay={
      <AbsoluteFill style={{ opacity: 0.88, zIndex: 0 }}>
        <Img
          src={staticFile("dajuesi/mec4_composite_eras.png")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    }
  />
);
