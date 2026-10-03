// Page06 — 万泉河畔：《三山五园图》水系带 PanZoom + 四方位 MapMarker（MEC-1）。
// 右下角说明卡落于纸雾区，纯 SVG 标���不入槽表。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

export const Page06: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[5] * VIDEO.fps);
  return (
    <MapPage
      page={6}
      background={
        <PanZoomView
          src="guajiatun/sanshanyuan_changchun_west_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 40, y: 180, scale: 1.12 }}
          durationInFrames={frames}
        >
          <MapMarker x={900} y={980} label="" color={PALETTE.ochre} radius={20} delay={60} />
          <MapMarker x={2400} y={760} label="" color={PALETTE.gold} radius={17} delay={130} />
          <MapMarker x={3300} y={620} label="" color={PALETTE.indigo} radius={17} delay={200} />
          <MapMarker x={500} y={1420} label="" color={PALETTE.indigo} radius={16} delay={270} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 620,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.92) 26%, rgba(247,240,223,0.97) 100%)",
          }}
        />
      }
    />
  );
};
