// pageMap.ts — E23 页长（秒）＝纯音频＋1.6s 尾垫。实测 2026-10-03。
// 同源链：PAGE_DURATIONS_SEC（含 1.6s 留白，供 Series offset 累加与 QA 抽帧）
// ← data/narration.ts PAGE_AUDIO_SEC（纯音频，供 Enter 锚点/字幕结算）。

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [36.18, 40.88, 35.68, 36.64, 38.17, 36.24, 32.51, 34.82];

export const TOTAL_FRAMES = PAGE_DURATIONS_SEC.reduce(
  (sum, s) => sum + Math.round(s * VIDEO.fps), 0,
);
