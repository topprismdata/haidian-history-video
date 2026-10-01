# Remotion 合成模板

八页 16:9 宣纸工笔淡彩风，E1–E10 全系列同管线。**新开一集从这里复制。**

```
remotion-template/
  package.json          依赖与命令
  src/
    index.tsx           注册入口
    Root.tsx            Composition 声明（1920×1080 @30fps）
    EpisodeCourse.tsx   时间轴：音频节拍 + 八页 Series
    SlotPage.tsx        填槽引擎（板面 PNG + DOM 文字）
    ui.tsx              PaperBg / EvidenceTag / PageCaptions
    data/
      pageMap.ts        页长与页起点  ← 要改
      narration.ts      配音节拍      ← 要改
      subtitles.ts      字幕分句      ← 要改
      slots.json        槽位几何      ← 由脚本生成
      pages.config.ts   槽位文案样式  ← 由脚本生成
    pages/Page01..08.tsx  八个页面壳
```

## 新开一集的改动清单

### 1. 装依赖

```bash
cp -r remotion-template <你的工程目录>
cd <你的工程目录>
npm install
```

### 2. 放素材

```
public/<集名>/
  page_01_layout.png … page_08_layout.png    板面，1672×941
public/audio/<集名>/
  p1.wav … p8.wav                              配音，24000Hz mono
```

> ⚠ 板面文件名**必须带 `_layout` 后缀**（生成端叫 `page_0N.png`）。
> 缺图不报错，只静默兜底成纯色背景。

### 3. 改四处

| 文件 | 改什么 |
|---|---|
| `src/EpisodeCourse.tsx` | `const EPISODE = "…"` |
| `src/SlotPage.tsx` | `const EPISODE = "…"`（板面目录名） |
| `src/data/pageMap.ts` | `PAGE_DURATIONS_SEC` 与 `AUDIO_SEC`，填实测值 |
| `src/data/narration.ts` | `PAGE_AUDIO`，同实测值 |

取实测时长：

```bash
for i in 1 2 3 4 5 6 7 8; do
  printf "p%d  " $i
  ffprobe -v error -show_entries format=duration -of csv=p=0 \
    public/audio/<集名>/p$i.wav
done
```

### 4. 生成槽位数据（不要手写）

```bash
python3 <集>_video/build_remotion_data.py
```

它从 `design.md` 读出全部槽位，写出 `data/slots.json` 与 `data/pages.config.ts`。

### 5. 逐页验收，再终渲染

```bash
npm run still -- --frame=<终态帧> out.png   # 单页检查
python3 scripts/qa_page.py                  # 程序化验全部 8 页
npm run render                              # 出片
```

## 终态帧怎么算

**页长与页起点是两套口径**，别混：

| 量 | 算法 |
|---|---|
| 页长（`durationInFrames`） | 纯音频 + 1.6s 页尾留白 |
| 页起点（`pageOffsetFrames`） | 前序各页**纯音频**累加，**不含**留白 |
| 终态帧 | 页起点 + 该页纯音频时长 × fps |

> **留白是页尾的，绝不能计入下一页起点。**
> E8 曾因此逐页漂移 0.4s、到 P7 累计 +9.6s（288 帧）——
> 抽 P7 的帧看到的是 P8 的内容，5 个验收代理误报"槽位空字"。
>
> 也不能取"纯音频末 − 0.5s"：末项进场按 anchor 铺满，取更早会漏
> （E9 P6 的 `compass` 实测页内 842 帧才出现，取 820 就缺它）。

## 字幕带会压住槽位

`PageCaptions` 固定 `bottom: 8`，内边距 14、字号 40、lineHeight 1.4
→ **高约 84px，占 y ≈ 988–1072，横跨全宽**。

槽位矩形相交检测**看不见它**（字幕条不是槽位）——设计阶段就要单独查这一层。
E9 有 5 处因此被压住，白渲一版才发现。
