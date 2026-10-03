// Page03 — 高梁河畔的归宿：全片核心证据页。
// PanZoomView 漫游《三山五园图》高梁河带 4000px 切片（MEC-1）：
// startView 全卷俯瞰 → endView 推至高梁河北岸台地一带（scale 1.25）。
// 呼吸圈 = MapMarker SVG 叠加（label 置空，命名走 backing tag 槽）；
// 引文横幅「葬于宛平之西原」出自元明善撰神道碑（考据修正后书证链）。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

// cover 基准：4000×2200 → scale1 显示 1964×1080（左右各裁 22px）。
// 地图点 (mx,my) → scale1 画布点 (mx*0.4909-22, my*0.4909)。
const toLayer = (mx: number, my: number): [number, number] => [mx * 0.4909 - 22, my * 0.4909];

export const Page03: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[2] * VIDEO.fps);
  const [riverX, riverY] = toLayer(900, 256); // 高梁河（今南长河）水道（图上蓝带）
  const [siteX, siteY] = toLayer(2350, 640); // 畏吾村故址方位（北岸台地）
  return (
    <MapPage
      page={3}
      background={
        <PanZoomView
          src="weigongcun/sanshanyuan_gaoliang_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 22, y: 210, scale: 1.25 }}
          durationInFrames={frames}
        >
          <MapMarker x={riverX} y={riverY} label="" color={PALETTE.indigo} radius={18} delay={40} />
          <MapMarker x={siteX} y={siteY} label="" color={PALETTE.ochre} radius={20} delay={200} />
        </PanZoomView>
      }
      overlay={
        /* 下部纸雾渐变：档案地图可读性处理——水网与双色圈保持全清晰，
           下部渐隐入卡纸色，引文横幅与考据卡落座其上。 */
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 720,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.95) 12%, rgba(247,240,223,0.98) 100%)",
          }}
        />
      }
    />
  );
};
