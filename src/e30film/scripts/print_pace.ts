// print_pace.ts — 测试对拍口: bun scripts/print_pace.ts 打印 pace 派生读数(JSON)。
// tests/test_p3_pace.py::test_remotion_pace_sourced 执行本脚本,
// 断言 TS 侧 duration/fps/段边界与真账 3d/out/film/pace.json 逐项一致。
import { E30_DURATION_IN_FRAMES, FILM_FPS, STAGE_CLIPS } from "../src/pace";

console.log(
  JSON.stringify({
    duration: E30_DURATION_IN_FRAMES,
    fps: FILM_FPS,
    stages: STAGE_CLIPS.length,
    first: STAGE_CLIPS[0],
    last: STAGE_CLIPS[STAGE_CLIPS.length - 1],
    clips: STAGE_CLIPS,
  }),
);
