# src/e30film — E30 十七孔桥建造动画 Remotion 合成

P3-T7 骨架。母版模式 = `/tmp/chemistry-video/src/shucun`(E11 SlotPage 管线),
但本工程时间轴**只来自 pace.json**, 禁 TS 自算帧号。

## 单一节奏源

```
e30_shikongqiao_video/3d/out/film/pace.json
    ↑ 生成: 3d/film/pace_build.py (T1)
    ↑ 唯一写通道: 3d/film/pace_writeback.py (T7, 音频秒→pad_frames)
    ← 只读消费: src/pace.ts (import 真账 JSON, 无副本)
```

fps / durationInFrames / Sequence 段边界 / 字幕窗 / 音频锚全部查表派生;
改动 pace 后 `bun scripts/print_pace.ts` 可直接看 TS 侧读数。

## 运行时接线(不入库, 本地重建)

```bash
bun install                                  # node_modules
ln -s ../../../e30_shikongqiao_video/3d/out/film/frames public/frames
mkdir -p public/audio                        # TTS 成品落这里(见下)
bun run typecheck                            # tsc --noEmit
bun run studio                               # 预览
bun run render                               # 出 out/e30film.mp4
```

`public/frames` 缺图=T8 试渲未跑, 渲染期缺帧即红(正确行为, 不做占位图)。

## 音频槽约定

- 文件: `public/audio/seg-01.mp3 … seg-05.mp3`(mlx 克隆音色既有管线产物)
- 锚: 各段 `from` = pace 边界(seg-01=帧 0 片头, seg-02=S001.start,
  seg-03=S009.start, seg-04=S386.start, seg-05=S392.start)
- 对齐: TTS 实测秒数写进 audio_table → `pace_writeback.py --audio-table`
  把超长音频补进对应 stage(pad_frames), 画面窗长自动追平音频。

## 段位(3d/film/narration_script.md)

| 槽 | 段 | pace 边界 |
|---|---|---|
| seg-01 | 开场 | 0(片头, pace 暂无前缀 stage, 零宽字幕窗) |
| seg-02 | 首孔教学 | S001 → S015 |
| seg-03 | 合龙 | S009 → S379 |
| seg-04 | 落架高潮 | S386 → S391 |
| seg-05 | 桥成 | S392 → S408 |
