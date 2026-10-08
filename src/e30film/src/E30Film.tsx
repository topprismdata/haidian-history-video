// E30Film — 十七孔桥逐石建造动画合成(1080p, fps/时长/段边界全部来自 pace.ts)。
// 帧图源: e30_shikongqiao_video/3d/out/film/frames/f%06d.png(Blender 无头驱动
// 产物, 经 public/frames 软链接入; T8 试渲前缺图属预期, 渲染期缺帧即红)。
// 音频槽: public/audio/seg-01..05.mp3(TTS 克隆音色成品, 锚=段边界)。
import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { E30_DURATION_IN_FRAMES, FILM_FPS } from "./pace";
import { SEGMENTS, audioAnchor } from "./segments";

export const E30_FPS: number = FILM_FPS;
export const E30_DURATION: number = E30_DURATION_IN_FRAMES;

// 帧图序列: 全局帧号直接映射 f%06d.png(不进子 Sequence, 免帧号换算)。
const FrameImage: React.FC = () => {
  const frame = useCurrentFrame();
  const src = staticFile(`frames/f${String(frame).padStart(6, "0")}.png`);
  return (
    <Img
      src={src}
      style={{ width: "100%", height: "100%", objectFit: "contain" }}
    />
  );
};

const Subtitles: React.FC<{ lines: string[] }> = ({ lines }) => (
  <div
    style={{
      position: "absolute",
      bottom: 48,
      left: 80,
      right: 80,
      textAlign: "center",
    }}
  >
    {lines.map((line, i) => (
      <div
        key={i}
        style={{
          color: "#fff",
          fontSize: 34,
          lineHeight: 1.6,
          textShadow: "0 2px 8px rgba(0,0,0,0.85)",
        }}
      >
        {line}
      </div>
    ))}
  </div>
);

export const E30Film: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#000" }}>
    <FrameImage />
    {SEGMENTS.map((seg) =>
      seg.to > seg.from ? (
        <Sequence
          key={seg.id}
          from={seg.from}
          durationInFrames={seg.to - seg.from}
          name={seg.label}
        >
          <Subtitles lines={seg.lines} />
        </Sequence>
      ) : null,
    )}
    {SEGMENTS.map((seg) => (
      <Sequence key={`aud-${seg.id}`} from={audioAnchor(seg)} name={`音频-${seg.id}`}>
        <Audio src={staticFile(`audio/${seg.id}.mp3`)} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
