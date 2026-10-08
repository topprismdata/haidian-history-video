# 音频槽

TTS(mlx 克隆音色, 既有管线)成品按 `seg-01.mp3 … seg-05.mp3` 落本目录,
对应 `src/segments.ts` 五段; 锚点=段边界帧(pace 同源)。

实测秒数须回写: 写 audio_table JSON(`{"S001": 12.3, …}`, 秒)后跑

    python3 3d/film/pace_writeback.py --pace 3d/out/film/pace.json \
        --audio-table audio_table.json

mp3/wav 不入库(可由 TTS 管线重建)。
