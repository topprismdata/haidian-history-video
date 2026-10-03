// narration.ts — E24《大觉寺·阳台山麓的千年清水院》配音节拍。实测 2026-10-03。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

const PAGE_AUDIO_SEC = [25.52, 37.60, 41.84, 33.52, 34.56, 40.72, 38.16, 39.36];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
