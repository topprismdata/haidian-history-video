// Page03 — 两套园址系统：全片第一张中央大地图。
// PanZoomView 漫游《三山五园图》4000px 切片（MEC-1）：
// startView 全图俯瞰 → endView 推沉至海淀一带（scale 1.6，落幅居中）。
// 双色方位圈 = MapMarker SVG 叠加（label 空，命名走 tag 槽）；非边界复原图。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

// cover 基准：4000×2400 → scale1 显示 1920×1152（上下各裁 36px）。
// 地图点 (mx,my) → scale1 画布点 (mx*0.48, my*0.48-36)。
const toLayer = (mx: number, my: number): [number, number] => [mx * 0.48, my * 0.48 - 36];

export const Page03: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[2] * VIDEO.fps);
  const [swX, swY] = toLayer(1450, 1080); // 勺园故址方位（西南）
  const [neX, neY] = toLayer(2750, 1150); // 和珅赐园方位（东北）
  return (
    <MapPage
      page={3}
      background={
        <PanZoomView
          src="shaoyuan/sanshanyuan_haidian_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: -230, y: 0, scale: 1.6 }}
          durationInFrames={frames}
        >
          <MapMarker x={swX} y={swY} label="" color={PALETTE.ochre} radius={22} delay={30} />
          <MapMarker x={neX} y={neY} label="" color={PALETTE.indigo} radius={22} delay={450} />
        </PanZoomView>
      }
      overlay={
        /* 下部纸雾渐变：档案地图 documentaries 标准可读性处理——
           双色圈与中景水网保持全清晰，下部街区带渐隐入卡纸色，
           文字卡落座其上。同时保证槽位平移负控制的落点无底图墨迹。 */
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 520,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.90) 21%, rgba(247,240,223,0.97) 100%)",
          }}
        />
      }
    />
  );
};
