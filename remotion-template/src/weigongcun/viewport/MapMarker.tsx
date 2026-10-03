import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * E21《魏公村·高梁河畔的畏吾村》分层视口引擎 — 地图呼吸定位标 (MapMarker)。
 *
 * 红线（E21 设计规范 / 全局约束）：
 * - 标记一律作为视口附属 SVG 叠加层渲染，严禁写入 slots.json 文字槽；
 * - 标签必须是 SVG <text> 矢量文本，严禁输出为外部 QA 可见的 DOM 文字槽；
 * - 呼吸光圈由 useCurrentFrame 驱动（0.5 Hz 正弦，逐帧确定性），
 *   入场弹性用 Remotion spring，而非时间基 CSS 动画。
 *
 * E21 特化：地理锚点面向 畏吾村（元）/ 魏村（明）/ 大慧寺 / 高梁河畔 / 白石桥，
 * 用法：作为 <PanZoomView> 的 children 放置，x/y 为视口容器内坐标，
 * 随底层地图同步推拉（贴附地理坐标点）。
 */

const BREATH_HZ = 0.5;
const LABEL_FONT = 20;

export const MapMarker: React.FC<{
  x: number;
  y: number;
  label: string;
  color?: string;
  radius?: number;
  delay?: number;
  breathHz?: number;
}> = ({ x, y, label, color = "#8b1a1a", radius = 10, delay = 0, breathHz = BREATH_HZ }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = Math.max(0, frame - delay);
  const pop = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 160 },
  });

  // 呼吸光圈：正弦确定性（同帧同值），外圈扩散 (1.5r → 2.5r) 同时变淡 (0.5 → 0.18)
  const breath = 0.5 + 0.5 * Math.sin((localFrame / fps) * Math.PI * 2 * breathHz);
  const ringR = radius * (1.5 + breath);
  const ringOpacity = 0.5 - 0.32 * breath;

  const w = 220;
  const h = 160;

  return (
    <svg
      width={w}
      height={h}
      viewBox={`${-w / 2} ${-h / 2} ${w} ${h}`}
      style={{
        position: "absolute",
        left: x - w / 2,
        top: y - h / 2,
        overflow: "visible",
        transform: `scale(${pop})`,
        transformOrigin: "center",
      }}
    >
        {/* 呼吸光圈 */}
        <circle
          cx={0}
          cy={0}
          r={ringR}
          fill="none"
          stroke={color}
          strokeWidth={2}
          opacity={ringOpacity}
        />
        {/* 定位内圈与核心点 */}
        <circle cx={0} cy={0} r={radius} fill={color} opacity={0.28} />
        <circle cx={0} cy={0} r={Math.max(3, radius * 0.45)} fill={color} />
        {/* 矢量标签：SVG text + 卡纸色描边保证古地图上可读 */}
        <text
          x={0}
          y={radius + 26}
          textAnchor="middle"
          fontSize={LABEL_FONT}
          fontWeight={700}
          fontFamily='"Songti SC", "STSong", "SimSun", serif'
          fill={color}
          stroke="#f7f0df"
          strokeWidth={4}
          paintOrder="stroke"
        >
          {label}
        </text>
    </svg>
  );
};
