// narration.ts — 每页一段配音的节拍。
// TODO: 把 AUDIO_SEC 换成实测值（见 pageMap.ts 注释里的 ffprobe 命令）。

export interface Beat { name: string; from: number; dur: number }

const PAGE_AUDIO = [21.6, 22.4, 25.6, 25.6, 21.8, 22.4, 26.0, 28.8];

/** 第 n 页（1-based）的音频节拍，单位秒 */
export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO[pageNo - 1] === undefined
    ? []
    : [{ name: `p${pageNo}`, from: 0, dur: PAGE_AUDIO[pageNo - 1] }];
