// pageMap.ts — E22 页长（秒）＝纯音频＋1.6s 尾垫。实测 2026-10-03。
// 同源链：PAGE_DURATIONS_SEC（含 1.6s 留白，供 Series offset 累加与 QA 抽帧）
// ← data/narration.ts PAGE_AUDIO_SEC（纯音频，供 Enter 锚点/字幕结算）。

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [32.40, 32.43, 38.16, 32.56, 35.84, 35.28, 28.72, 35.44];

export const TOTAL_FRAMES = PAGE_DURATIONS_SEC.reduce(
  (sum, s) => sum + Math.round(s * VIDEO.fps), 0,
);
