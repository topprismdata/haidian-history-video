// Page08 — 七百年，一座活着的纪念碑：MEC-4 四时代叠合图收官。
// 叠合图（元代畏吾村/明代佛刹/清代长河水道/当代高校街区，纯图形零文字）
// 以极缓推镜落幅；四个时代由 backing tag 芯片命名。
import React from "react";
import { MapPage } from "../SlotPage";
import { PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";

export const Page08: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[7] * VIDEO.fps);
  return (
    <MapPage
      page={8}
      background={
        <PanZoomView
          src="weigongcun/mec4_composite_eras.png"
          startView={{ x: 0, y: 0, scale: 1.06 }}
          endView={{ x: 0, y: 0, scale: 1 }}
          durationInFrames={frames}
        />
      }
    />
  );
};
