// Page04 — 西郊赐第：《三山五园图》畅春园西侧万泉河带 PanZoom（MEC-1）。
// 下部纸雾渐变：档案地图可读性处理，确保文字槽与负控制绝对干净。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

export const Page04: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[3] * VIDEO.fps);
  return (
    <MapPage
      page={4}
      background={
        <PanZoomView
          src="guajiatun/sanshanyuan_changchun_west_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 60, y: 120, scale: 1.18 }}
          durationInFrames={frames}
        >
          {/* 额驸城遗址方位（西侧台地） */}
          <MapMarker x={820} y={180} label="" color={PALETTE.ochre} radius={20} delay={90} />
          {/* 畅春园西墙 */}
          <MapMarker x={3120} y={420} label="" color={PALETTE.gold} radius={18} delay={200} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 400,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.95) 12%, rgba(247,240,223,0.98) 100%)",
          }}
        />
      }
    />
  );
};
