// pace.ts — pace.json 是唯一节奏源: fps/总帧数/段边界一律查本表,
// 本工程禁自算帧号(tests/test_p3_pace.py::test_remotion_pace_sourced grep 把关)。
// 真账: e30_shikongqiao_video/3d/out/film/pace.json(T1 生成;
// 唯一写通道 = 3d/film/pace_writeback.py, 音频秒数→pad_frames)。
import paceJson from "../../../e30_shikongqiao_video/3d/out/film/pace.json";

export const PACE = paceJson;
export type PaceStage = (typeof PACE.stages)[number];

export const FILM_FPS: number = PACE.fps;
export const E30_DURATION_IN_FRAMES: number = PACE.total_frames;

export interface StageClip {
  id: string;
  from: number;
  to: number;
}

export const STAGE_CLIPS: StageClip[] = PACE.stages.map((s: PaceStage) => ({
  id: s.id,
  from: s.start,
  to: s.end,
}));

const CLIP_BY_ID: Record<string, StageClip> = Object.fromEntries(
  STAGE_CLIPS.map((c) => [c.id, c]),
);

const clip = (id: string): StageClip => {
  const c = CLIP_BY_ID[id];
  if (!c) {
    throw new Error(`pace.json 无 stage ${id}(锚点 id 拼写错误?)`);
  }
  return c;
};

export const stageStart = (id: string): number => clip(id).from;
export const stageEnd = (id: string): number => clip(id).to;
