// narration.ts — E24《大觉寺·阳台山麓的千年清水院》配音节拍。实测 2026-10-03。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

const PAGE_AUDIO_SEC = [25.12, 34.88, 42.72, 35.76, 33.92, 37.20, 35.12, 38.56];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
