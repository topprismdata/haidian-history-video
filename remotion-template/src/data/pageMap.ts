// pageMap.ts — 页长与全局尺寸。
//
// ⚠ 两套口径，用途不同（E8 在这里踩过坑，累计 288 帧漂移）：
//   页长   = 纯音频 + 1.6s 页尾留白  -> Series.Sequence durationInFrames
//   页起点 = 前序各页**纯音频**累加    -> pageOffsetFrames / 槽位 bounds
//   留白是页尾的，绝不能计入下一页起点。
//
// TODO: 用实测音频时长替换下面的占位值。
//   for i in 1..8: ffprobe -v error -show_entries format=duration -of csv=p=0 audio/<集>/pN.wav

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

/** 每页时长（秒）= 纯音频 + 1.6 */
export const PAGE_DURATIONS_SEC = [
  23.2,   // p01  ← TODO 实测
  27.28,  // p02
  34.04,  // p03
  30.0,   // p04
  26.56,  // p05
  26.8,   // p06
  30.48,  // p07
  33.84,  // p08
];

/** 各页**纯音频**时长（秒），用于算页起点 */
export const AUDIO_SEC = [
  21.6, 22.4, 25.6, 25.6, 21.8, 22.4, 26.0, 28.8,
];
