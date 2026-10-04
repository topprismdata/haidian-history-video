// narration.ts — E29《郭守敬·一泉入都》配音节拍。实测 2026-10-04。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

const PAGE_AUDIO_SEC = [33.28, 37.76, 35.12, 36.00, 29.44, 36.96, 37.52, 37.84];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
