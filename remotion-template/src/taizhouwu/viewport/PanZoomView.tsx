import React from "react";
import { Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

/**
 * E22《太舟坞·唐代羁縻带州与元代船坞之谜》分层视口引擎 — 底层视口：平滑推拉漫游 (Pan-Zoom)。
 *
 * 复用 E20 黄金数学契约（与 tests/test_taizhouwu_viewport.py 黄金模型同源）：
 * - 进度 clamp 到 [0, 1]，帧越界不外推 (extrapolate clamp)；
 * - durationInFrames <= 0 视为已完成，Math.max(1, …) 防除零与 inputRange 非单调；
 * - 缓动 = cubic-bezier(0.25, 0.1, 0.25, 1.0)（起幅平缓、落幅稳定、无过冲）；
 * - transform: translate3d(...) scale(...) 走 GPU 合成，外层 overflow: hidden 裁切。
 *
 * E21 特化：
 * - 底图面向《三山五园图》高梁河带 4000px 切片与 1915《实测京师四郊图》魏公村切片；
 * - fit 属性支持 cover（默认，铺满裁切）/ contain（完整装裱展示书影类资产）。
 */

export type ViewSpec = {
  x: number;
  y: number;
  scale: number;
};

const EASE = Easing.bezier(0.25, 0.1, 0.25, 1.0);

export const PanZoomView: React.FC<{
  src: string;
  startView: ViewSpec;
  endView: ViewSpec;
  durationInFrames?: number;
  fit?: "cover" | "contain";
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ src, startView, endView, durationInFrames = 90, fit = "cover", style, children }) => {
  const frame = useCurrentFrame();
  const safeDuration = Math.max(1, Math.round(durationInFrames));
  const progress = interpolate(frame, [0, safeDuration], [0, 1], {
    easing: EASE,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const lerp = (a: number, b: number): number => a + (b - a) * progress;
  const x = lerp(startView.x, endView.x);
  const y = lerp(startView.y, endView.y);
  const scale = lerp(startView.scale, endView.scale);

  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        width: "100%",
        height: "100%",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          transform: `translate3d(${x}px, ${y}px, 0) scale(${scale})`,
          transformOrigin: "center center",
          willChange: "transform",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: fit,
            display: "block",
          }}
        />
        {/* children = 贴附在底图地理坐标上的 SVG 叠加层（如 MapMarker），随视口同步推拉 */}
        {children}
      </div>
    </div>
  );
};
